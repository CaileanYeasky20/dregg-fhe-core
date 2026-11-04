//! Independent checker for the `m31-vmatmul/v1` relation.
//! Semantics: `lean/Engine.lean`. Bytes: normative in `ref/m31ref.py`.
#![forbid(unsafe_code)]

use sha2::{Digest, Sha256};

pub const P: u64 = (1 << 31) - 1;
pub const HALF: u64 = (P - 1) / 2;
pub const REPS: usize = 6;

pub type Matrix = Vec<Vec<u64>>;

#[derive(Debug, PartialEq, Eq)]
pub enum VerifyError {
    Empty(&'static str),
    TooLarge(&'static str),
    Ragged(&'static str),
    NonCanonical(&'static str),
    Shape,
    Freivalds,
    Relu,
}

fn check(name: &'static str, m: &Matrix) -> Result<(usize, usize), VerifyError> {
    let rows = m.len();
    let cols = m.first().map_or(0, |r| r.len());
    if rows == 0 || cols == 0 {
        return Err(VerifyError::Empty(name));
    }
    if u32::try_from(rows).is_err() || u32::try_from(cols).is_err() {
        return Err(VerifyError::TooLarge(name));
    }
    for r in m {
        if r.len() != cols {
            return Err(VerifyError::Ragged(name));
        }
        if r.iter().any(|&x| x >= P) {
            return Err(VerifyError::NonCanonical(name));
        }
    }
    Ok((rows, cols))
}

pub fn tensor_digest(m: &Matrix) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"m31-vmatmul/v1/tensor");
    h.update((m.len() as u32).to_be_bytes());
    h.update((m.first().map_or(0, |r| r.len()) as u32).to_be_bytes());
    for row in m {
        for &x in row {
            h.update((x as u32).to_be_bytes());
        }
    }
    h.finalize().into()
}

pub fn challenge_seed(a: &Matrix, b: &Matrix, c: &Matrix) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"m31-vmatmul/v1/challenge");
    h.update(tensor_digest(a));
    h.update(tensor_digest(b));
    h.update(tensor_digest(c));
    h.finalize().into()
}

pub fn sample_field(seed: &[u8; 32], t: u32, l: u32) -> u64 {
    let mut ctr: u32 = 0;
    loop {
        let mut h = Sha256::new();
        h.update(b"m31-vmatmul/v1/beta");
        h.update(seed);
        h.update(t.to_be_bytes());
        h.update(l.to_be_bytes());
        h.update(ctr.to_be_bytes());
        let d = h.finalize();
        let v = u64::from(u32::from_be_bytes([d[0], d[1], d[2], d[3]]) & 0x7FFF_FFFF);
        if v < P {
            return v;
        }
        ctr += 1;
    }
}

fn matvec(m: &Matrix, v: &[u64]) -> Vec<u64> {
    m.iter()
        .map(|row| row.iter().zip(v).fold(0u64, |acc, (&a, &x)| (acc + a * x % P) % P))
        .collect()
}

pub fn verify_matmul(a: &Matrix, b: &Matrix, c: &Matrix) -> Result<(), VerifyError> {
    let (m, n) = check("A", a)?;
    let (n2, k) = check("B", b)?;
    let (m2, k2) = check("C", c)?;
    if (m, n, k) != (m2, n2, k2) {
        return Err(VerifyError::Shape);
    }
    let seed = challenge_seed(a, b, c);
    for t in 0..REPS {
        let beta: Vec<u64> = (0..k).map(|l| sample_field(&seed, t as u32, l as u32)).collect();
        if matvec(a, &matvec(b, &beta)) != matvec(c, &beta) {
            return Err(VerifyError::Freivalds);
        }
    }
    Ok(())
}

pub fn relu(x: u64) -> u64 {
    if x <= HALF { x } else { 0 }
}

pub fn verify_layer(a: &Matrix, b: &Matrix, c: &Matrix, y: &Matrix) -> Result<(), VerifyError> {
    verify_matmul(a, b, c)?;
    check("Y", y)?;
    let expect: Matrix = c.iter().map(|r| r.iter().map(|&x| relu(x)).collect()).collect();
    if &expect != y {
        return Err(VerifyError::Relu);
    }
    Ok(())
}

pub fn statement_digest(a: &Matrix, b: &Matrix, c: &Matrix, y: &Matrix) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"m31-vmatmul/v1/stmt");
    for x in [a, b, c, y] {
        h.update(tensor_digest(x));
    }
    h.finalize().into()
}

pub fn genesis() -> [u8; 32] {
    Sha256::digest(b"m31-vmatmul/v1/genesis").into()
}

pub fn chain_fold(prev: &[u8; 32], stmt: &[u8; 32], index: u32) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"m31-vmatmul/v1/chain");
    h.update(prev);
    h.update(index.to_be_bytes());
    h.update(stmt);
    h.finalize().into()
}
