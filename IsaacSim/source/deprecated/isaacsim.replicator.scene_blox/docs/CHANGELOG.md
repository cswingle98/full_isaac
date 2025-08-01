# Changelog

## [1.0.8] - 2025-05-22
### Changed
- Update copyright and license to apache v2.0

## [1.0.7] - 2025-05-21
### Changed
- Extension deprecated since Isaac Sim 5.0.0.

## [1.0.6] - 2025-05-16
### Changed
- Make extension target a specific kit version

## [1.0.5] - 2025-04-17
### Changed
- changed add_update_semantics to add_labels

## [1.0.4] - 2025-04-04
### Changed
- Version bump to fix extension publishing issues

## [1.0.3] - 2025-03-26
### Changed
- Cleanup and standardize extension.toml, update code formatting for all code

## [1.0.2] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [1.0.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [1.0.0] - 2024-09-23
### Changed
- Extension renamed to isaacsim.replicator.scene_blox

## [0.1.2] - 2024-02-02
### Changed
- Updated path to the nucleus extension

## [0.1.1] - 2023-03-20
### Changed

- Updates all modules to use newly-added global RNG, enabling replicability by setting seed.

### Added

- omni.isaac.scene_blox.grid_utils.config - Maintains global RNG.

## [0.1.0] - 2023-01-17
### Changed

- Moved to omni.isaac.scene_blox

## [0.0.5] - 2022-08-01
### Fixed

- bug where app would hang on exit
- error message on stage close

## [0.0.4] - 2022-08-01
### Changed

- Assets path may now be out of the /Isaac folder

### Added

- If a variant name is "*", a variant value is selected at random for all variants

## [0.0.3] - 2022-06-02
### Changed

- Removed livesync option which was unstable and not useful

## [0.0.2] - 2022-05-20
### Fixed

- Issue on prim path formatting on Windows (was using OS-style separator instead of /)

### Changed

- Adding a try - except on main file to warn users to install module with pip before trying to use it
