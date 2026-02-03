# Master Attendance Workflow (Phases 1-5)
This document serves as the comprehensive operational guide for the Attendance Module, covering all planned phases from core manual operations to full RFID automation.

## 🟦 PART A: CORE OPERATIONS (Phase 1)
### 1. System Configuration
**Prerequisite**: Ensure Academic Year, Program, Department, Faculty, and Student Master data is populated.

- **Settings**: Configure Attendance Settings (Min %, Course Hours).
- **Timetable**: Create Course Schedule for all active courses.

### 2. Daily Attendance Recording
**Method 1: Manual Marking**
1. Faculty/Admin creates an `Attendance Session` based on the schedule or ad-hoc.
2. Selects Course Offering and Instructor.
3. Marks status for each student: Present, Absent, Late, Excused.
4. **Submit**: Triggers calculation.

**Method 2: Office Hours**
1. Faculty creates `Office Hours Session`.
2. Student/Faculty logs check-in and check-out times.
3. System adds duration to coverage.

### 3. Automated Calculations
**Trigger**: Real-time on every attendance submission/update.
**Logic**:
- Updates `attendance_percentage = (Sessions Attended / Sessions Conducted) * 100`.
- Determines `eligibility_status` (Eligible/Shortage/Critical) based on 75% threshold.

## 🟦 PART B: EXCEPTIONS & CONDONATION (Phase 2)
### 1. Condonation Workflow
Handle attendance shortage due to medical or official reasons.

- **Application**: Student applies via `Attendance Condonation` form with proof (Medical Cert).
- **Review**: Faculty recommends -> Principal/Dean approves.
- **Impact**:
    - Approved "Condonation Hours" are added to the student's attended count.
    - Percentage is recalculated: `(Attended + Condonation) / Total`.

### 2. Exam Eligibility List
Automated generation of eligible/detained lists before exams.

- **Freeze Data**: Admin sets a cutoff date.
- **Generate Lists**:
    - **Eligible**: >75%.
    - **Condonable Shortage**: 65% - 75% (Fine applicable).
    - **Detained**: <65% (Critical).
- **Action**: Block/Release Hall Tickets based on list status.

## 🟦 PART C: REPORTING & ANALYTICS (Phase 3)
### 1. Dashboards
- **Student**: View personal attendance %, shortage alerts, and attendance history.
- **Faculty**: View class-wise trends, identifying frequent absentees.
- **Admin**: Program-level compliance reports and compliance metrics.

### 2. Standard Reports
- **Daily Absentees**: List of students absent today.
- **Consecutive Absents**: Alert for students missing >3 days in a row.
- **Course Completion**: Track if planned course hours (e.g., 40h) are met.

## 🟦 PART D: RFID INFRASTRUCTURE (Phase 4)
### 1. Data Preparation
- **Tag Generation**: Assign unique RFID UID to every `Student Master`.
- **Device Setup**: Register readers in `RFID Device` DocType (Location, IP, Status).

### 2. Log Capture (No Processing)
- **Activity**: swipes are captured in `Attendance Log` raw table.
- **Validation**: System checks valid UID but takes no attendance action yet.

## 🟦 PART E: RFID INTEGRATION (Phase 5)
### 1. Automated Attendance Flow
- **Swipe**: Student taps ID card on reader.
- **Device Auth**: Reader authenticates via API Token.
- **Log Entry**: Data sent to `Attendance Log` (UID, Timestamp, Device ID).
- **Processing Job**:
    - System matches Device Location + Time to active `Course Schedule`.
    - Identifies the `Attendance Session`.
- **Record Creation**:
    - Finds Student by RFID UID.
    - Creates/Updates `Student Attendance` record as Present.
- **Anti-Flood**: Ignores duplicate swipes within X minutes.

### 2. Fallback & Reconciliation
- **Missing Swipes**: Faculty can manually override "Absent" to "Present" if RFID failed.
- **Device Failure**: Alerts triggered if device goes offline; switching to Manual Marking mode.

### 3. Final Verification
- **Dashboard monitors** "Real-time Swipes".
- **Comparison report**: Calculated vs. Actual physical headcounts.
