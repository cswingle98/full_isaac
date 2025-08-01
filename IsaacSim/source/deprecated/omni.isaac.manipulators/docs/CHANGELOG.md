# Changelog
## [3.0.7] - 2025-05-19
### Changed
- Update copyright and license to apache v2.0

## [3.0.6] - 2025-04-04
### Changed
- Version bump to fix extension publishing issues

## [3.0.5] - 2025-03-26
### Changed
- Cleanup and standardize extension.toml, update code formatting for all code

## [3.0.4] - 2025-03-25
### Changed
- Add import tests for deprecated extensions

## [3.0.3] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [3.0.2] - 2025-01-21
### Fixed
- Corrected module import.

## [3.0.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [3.0.0] - 2024-09-30
### Deprecated
- Extension deprecated since Isaac Sim 4.5.0. Replaced by isaacsim.robot.manipulators

## [2.1.1] - 2024-09-28
### Added
- isaacsim.robot.surface_gripper extension rename

## [2.1.0] - 2024-05-24
### Added
- end_effector_prim_path argument added to the SingleManipulator alongside the end_effector_prim_name

## [2.0.0] - 2024-03-26
### Changed
- Extension factored into multiple components.  See omni.isaac.manipulators.ui

## [1.3.1] - 2024-03-21
### Changed
- enabled "add to existing graph" for all the shortcuts

## [1.3.0] - 2024-03-15
### Changed
- moved all python code into a python folder. deleted omni/isaac/manipulators

### Added
- Gripper Controller Node
- automatically populated omnigraph for gripper controller
- pointer to open up the python script that generates the omnigraph for the menu shortcut graphs

## [1.2.0] - 2024-02-07
### Added
- a menu item for the extension to allow for populating common controller omnigraphs
- automatically populated omnigraph for position and velocity controller of any articulation object

## [1.1.0] - 2022-11-24
### Added
- Add functionality to run only first x phases of the pick and place controller (instead of full 10)
- Change parameter name in controller initialization
- Add documentation

## [1.0.2] - 2022-11-22
### Fixed
- Fix typo in `suction_gripper.py` warning message

## [1.0.1] - 2022-08-03
### Fixed
- Bugfix `parallel_gripper.py` `apply_action` internally calling wrong function.

## [1.0.0] - 2022-07-26
### Added
- Added Manipulator class
