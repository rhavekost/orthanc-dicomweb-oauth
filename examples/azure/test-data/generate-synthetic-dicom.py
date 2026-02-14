#!/usr/bin/env python3
"""
Generate synthetic DICOM data for testing Azure Orthanc deployments.

Creates a sample CT study with 2 series (20 total images):
- Series 1: Axial CT (10 slices)
- Series 2: Coronal CT (10 slices)

No PHI, safe for public repositories.
"""

import sys
from datetime import datetime
from pathlib import Path

try:
    import numpy as np
    from pydicom.dataset import Dataset, FileDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid
except ImportError:
    print("Error: Required packages not found.")
    print("Please install: pip install pydicom numpy pillow")
    sys.exit(1)


def create_synthetic_image(
    width: int = 512, height: int = 512, slice_num: int = 0
) -> np.ndarray:
    """Create a synthetic CT image with realistic-looking patterns."""
    # Create base noise
    image = np.random.normal(1000, 200, (height, width))

    # Add circular phantom (simulates body)
    y, x = np.ogrid[:height, :width]
    center_y, center_x = height // 2, width // 2
    radius = min(height, width) // 3

    # Body circle
    mask = (x - center_x) ** 2 + (y - center_y) ** 2 <= radius**2
    image[mask] = np.random.normal(50, 10, np.sum(mask))  # Soft tissue

    # Add some "organs" (circles with different densities)
    organ1_x, organ1_y = center_x - 80, center_y - 50
    organ1_radius = 40
    organ1_mask = (x - organ1_x) ** 2 + (y - organ1_y) ** 2 <= organ1_radius**2
    image[organ1_mask] = np.random.normal(30, 5, np.sum(organ1_mask))

    organ2_x, organ2_y = center_x + 70, center_y - 30
    organ2_radius = 50
    organ2_mask = (x - organ2_x) ** 2 + (y - organ2_y) ** 2 <= organ2_radius**2
    image[organ2_mask] = np.random.normal(20, 5, np.sum(organ2_mask))

    # Add slice-dependent variation
    image = image + (slice_num - 5) * 10

    # Clip to valid CT range and convert to uint16
    image = np.clip(image, -1024, 3071)
    image = (image + 1024).astype(np.uint16)

    return image


def create_dicom_file(
    output_path: Path,
    patient_name: str,
    patient_id: str,
    study_uid: str,
    series_uid: str,
    series_number: int,
    series_description: str,
    instance_number: int,
    slice_location: float,
    image_data: np.ndarray,
) -> None:
    """Create a DICOM file with synthetic data."""

    # Generate unique instance UID
    instance_uid = generate_uid()

    # Create file meta information
    file_meta = Dataset()
    file_meta.FileMetaInformationGroupLength = 192
    file_meta.FileMetaInformationVersion = b"\x00\x01"
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = instance_uid
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_uid()
    file_meta.ImplementationVersionName = "SYNTH_1.0"

    # Create the FileDataset instance
    ds = FileDataset(str(output_path), {}, file_meta=file_meta, preamble=b"\0" * 128)

    # Set creation date/time
    dt = datetime.now()

    # Patient Module
    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.PatientBirthDate = "19700101"  # Synthetic
    ds.PatientSex = "O"  # Other (de-identified)

    # General Study Module
    ds.StudyInstanceUID = study_uid
    ds.StudyDate = dt.strftime("%Y%m%d")
    ds.StudyTime = dt.strftime("%H%M%S")
    ds.StudyID = "SYNTH001"
    ds.AccessionNumber = "ACC" + dt.strftime("%Y%m%d%H%M%S")
    ds.ReferringPhysicianName = "SYNTHETIC^DATA"
    ds.StudyDescription = "Synthetic CT Study"

    # General Series Module
    ds.SeriesInstanceUID = series_uid
    ds.SeriesNumber = series_number
    ds.SeriesDescription = series_description
    ds.Modality = "CT"
    ds.SeriesDate = dt.strftime("%Y%m%d")
    ds.SeriesTime = dt.strftime("%H%M%S")

    # General Equipment Module
    ds.Manufacturer = "Synthetic Devices Inc"
    ds.ManufacturerModelName = "SyntheticCT-3000"
    ds.SoftwareVersions = "1.0"

    # General Image Module
    ds.InstanceNumber = instance_number
    ds.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
    ds.ContentDate = dt.strftime("%Y%m%d")
    ds.ContentTime = dt.strftime("%H%M%S")

    # Image Plane Module
    ds.SliceThickness = 2.5
    ds.SliceLocation = slice_location
    ds.ImagePositionPatient = [0, 0, slice_location]
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.PixelSpacing = [0.5, 0.5]

    # Image Pixel Module
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = image_data.shape[0]
    ds.Columns = image_data.shape[1]
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0  # Unsigned
    ds.PixelData = image_data.tobytes()

    # CT Image Module
    ds.RescaleIntercept = -1024
    ds.RescaleSlope = 1
    ds.KVP = 120

    # SOP Common Module
    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"  # CT Image Storage
    ds.SOPInstanceUID = instance_uid

    # Save the DICOM file
    ds.save_as(str(output_path), write_like_original=False)
    print(f"  Created: {output_path.name}")


def main() -> None:
    """Generate synthetic DICOM test data."""

    # Create output directory
    output_dir = Path(__file__).parent / "sample-study"
    output_dir.mkdir(exist_ok=True)

    print("Generating synthetic DICOM test data...")
    print(f"Output directory: {output_dir}")
    print()

    # Generate UIDs for study and series
    study_uid = generate_uid()
    series1_uid = generate_uid()
    series2_uid = generate_uid()

    # Patient information (synthetic)
    patient_name = "TEST^PATIENT^001"
    patient_id = "TEST-001"

    # Generate Series 1: Axial CT (10 slices)
    print("Series 1: Axial CT (10 slices)")
    for i in range(10):
        image_data = create_synthetic_image(slice_num=i)
        output_path = output_dir / f"CT_AXIAL_{i+1:03d}.dcm"
        create_dicom_file(
            output_path=output_path,
            patient_name=patient_name,
            patient_id=patient_id,
            study_uid=study_uid,
            series_uid=series1_uid,
            series_number=1,
            series_description="Axial CT",
            instance_number=i + 1,
            slice_location=i * 2.5,
            image_data=image_data,
        )

    print()
    print("Series 2: Coronal CT (10 slices)")
    for i in range(10):
        image_data = create_synthetic_image(slice_num=i)
        output_path = output_dir / f"CT_CORONAL_{i+1:03d}.dcm"
        create_dicom_file(
            output_path=output_path,
            patient_name=patient_name,
            patient_id=patient_id,
            study_uid=study_uid,
            series_uid=series2_uid,
            series_number=2,
            series_description="Coronal CT",
            instance_number=i + 1,
            slice_location=i * 2.5,
            image_data=image_data,
        )

    print()
    print("✅ Successfully generated 20 synthetic DICOM files")
    print(f"   Study UID: {study_uid}")
    print(f"   Patient: {patient_name} ({patient_id})")
    print()
    print("Next steps:")
    print("  1. Deploy Azure environment (quickstart or production)")
    print("  2. Upload test data using upload-test-data.sh")
    print("  3. Verify in Orthanc web UI")


if __name__ == "__main__":
    main()
