## Purpose

Detects the player's face landmarks and face bounding box from the webcam feed
using the MediaPipe Tasks API FaceLandmarker (`models/face_landmarker.task`),
providing tighter face-crop regions than the legacy FaceMesh solution API.

## Requirements

### Requirement: Face landmark detection via Tasks API

The system SHALL detect the player's face from the webcam feed using the
MediaPipe Tasks API `FaceLandmarker` with the `models/face_landmarker.task`
model file.

#### Scenario: Face landmarks detected

- **WHEN** the player is in front of the camera with their face visible
- **THEN** the system runs `FaceLandmarker` in VIDEO mode on the RGB camera
  frame using the `face_landmarker.task` model
- **AND** returns 468 normalized face landmarks for the first detected face
- **AND** returns a face bounding box (when the model version supports it)
  describing the face region

#### Scenario: Face landmark model loaded from task file

- **WHEN** the application starts and `models/face_landmarker.task` does not
  exist
- **THEN** the system downloads the model file from the MediaPipe model
  registry
- **AND** if the download fails, the system falls back to the existing
  FaceMesh solution API detector without crashing

#### Scenario: No face detected

- **WHEN** the player's face is not visible or FaceLandmarker fails to detect
- **THEN** the detector returns no face landmarks and no bounding box
- **AND** the caller falls back to the existing Mario head circle rendering

### Requirement: Face bounding box output

The system SHALL expose the face bounding box returned by the FaceLandmarker
so the face cropper can compute tighter crop regions.

#### Scenario: Bounding box provided to cropper

- **WHEN** FaceLandmarker returns a face bounding box
- **THEN** the face cropper uses the bounding box origin and dimensions to
  determine the face crop region
- **AND** the crop is centered more precisely on the face than the
  contour-landmark heuristic

#### Scenario: Bounding box absent in legacy model versions

- **WHEN** the FaceLandmarker model version does not provide a face bounding
  box
- **THEN** the face cropper falls back to using face contour landmarks
  (indices 1–200) to estimate the face boundary
- **AND** cropping still succeeds without errors
