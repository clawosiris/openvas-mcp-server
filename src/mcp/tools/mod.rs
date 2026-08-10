//! Tool implementations, one module per toolset. Each module contributes a
//! named router (`<toolset>_router`) that [`super::server`] composes
//! according to the active toolset selection and read-only mode.

pub mod common;
pub mod system;
pub mod targets;
pub mod tasks;
