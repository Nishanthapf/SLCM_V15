# Deep Dive: Student Attendance System

This document provides a comprehensive technical guide to the core entities (DocTypes) that power the Student Attendance System.

---

## 1. Student Attendance

### Purpose
The **Student Attendance** DocType is the atomic unit of the attendance system. It represents a single student's status (Present/Absent/On Leave) for a specific learning activity (Lecture, Tutorial, or Office Hour).

### Key Features
*   **Unified Model**: Whether it's a Lecture or an Office Hour, all records are stored here.
*   **Duplicate Protection**: Built-in validation prevents multiple records for the same student/session pair.
*   **Audit Trail**: Tracks changes (e.g., from Absent to Present) with reasons, maintaining a history in `Attendance Edit Log`.
*   **Lock Mechanism**: Blocks edits to records older than `attendance_lock_days` (configured in Settings).

### Advantages
*   **Granularity**: Allows precise tracking down to the specific session level.
*   **Auditability**: Instructor changes are logged, ensuring accountability.
*   **Flexibility**: Supports various "Session Types" (Lecture, Lab, Office Hour) with different weighting via `hours_counted`.

### Disadvantages
*   **Volume**: Generates millions of records over time. Requires aggressive archiving or partitioning strategies for large universities.

---

## 2. Attendance Log

### Purpose
The **Attendance Log** captures raw temporal events, primarily from RFID swipes or biometric devices. It acts as the "staging area" for attendance data.

### Key Features
*   **Immutable Raw Data**: Represents the undeniable fact that "Card X swiped at Reader Y at Time Z".
*   **Async Processing**: Logs are inserted rapidly and processed asynchronously to create actual `Student Attendance` records.
*   **Status Tracking**: Tracks processing state (`Unprocessed`, `Processed`, `Error`) to ensure no data is lost.

### Advantages
*   **Decoupling**: Separates hardware events from business logic. If the logic fails (e.g., bug in session matching), the raw log remains safe for re-processing.
*   **Performance**: High-speed ingestion (e.g., thousands of swipes during class changeover) doesn't block the main database.

### Disadvantages
*   **Noise**: Can contain "junk" data (double swipes, passersby) that requires complex filtering logic.
*   **Hardware Dependency**: Relies on the clock synchronization of the reader devices.

---

## 3. Student Attendance Condonation

### Purpose
Allows students to request forgiveness for missed classes due to valid reasons (Medical, Personal). Instead of changing "Absent" to "Present", it adds "Condoned Hours" to the total attended duration.

### Key Features
*   **Workflow Integration**: Triggers an approval process (Student apply -> Chair approve).
*   **Evidence-Based**: Requires attachment of proof documents (e.g., Medical Certificate).
*   **Auto-Calculation**: On approval, automatically recalculates the student's attendance percentage.

### Advantages
*   **Compliance**: Formalizes the "medical leave" process, removing ad-hoc manual adjustments.
*   **Transparency**: Student sees exactly how many hours were condoned and why.

### Disadvantages
*   **Misuse Risk**: Requires strict manual verification of attached documents to prevent fraud.

---

## 4. FA / MFA Application

### Purpose
Manages **First Attempt (FA)** and **Medical First Attempt (MFA)** requests. This is the "Safety Valve" of the system: it overrides strict attendance rules to allow a student to sit for exams despite having low attendance (< 75%).

### Key Features
*   **Logic Override**: An approved FA/MFA acts as a "Golden Ticket". It forces `Eligible for Exam = YES` in the Attendance Summary regardless of the actual percentage.
*   **Strict Validation**:
    *   **University Representation**: Validates that the event dates are within 3 days of the exam.
    *   **Deadlines**: Checks if the application is submitted within the allowed window before/after exams.

### Advantages
*   **Policy Enforcement**: Automates complex university regulations regarding exam eligibility.
*   **Risk Mitigation**: Ensures students with genuine reasons (e.g., representing the university in sports) aren't unfairly penalized.

### Disadvantages
*   **Complexity**: The rules for "eligibility" become complex logic trees (Percentage > 75% OR FA Approved OR MFA Approved).

---

## 5. Attendance Session

### Purpose
The **Attendance Session** is the "Container" for class attendance. It represents a specific instance of a class (e.g., "Math 101 on Monday at 9 AM").

### Key Features
*   **Batch Processing**: One session object manages the creation of attendance records for all enrolled students.
*   **Validation**: Ensures classes are only conducted during valid scheduled times.
*   **Reporting**: Provides a session-by-session breakdown of attendance trends.

### Advantages
*   **Efficiency**: Significant reduction in manual data entry.
*   **Accuracy**: Links attendance directly to the specific topic/instructor for that hour.

### Disadvantages
*   **Scheduling Rigidity**: Requires the `Course Schedule` to be 100% accurate. Last-minute room or time changes must be updated in the system for RFID matching to work.

---

## Summary Diagram

```mermaid
graph TD
    Raw[Attendance Log] -->|Process| Session[Attendance Session]
    Session -->|Generates| SA[Student Attendance]
    
    Cond[Condonation] -->|Adds Hours| Calc[Attendance Calculator]
    SA -->|Feeds| Calc
    
    Calc -->|Updates| Summary[Attendance Summary]
    
    FA[FA/MFA App] -->|Overrides| Eligibility{Eligible for Exam?}
    Summary -->|Check %| Eligibility
```

---

## 6. Attendance Settings

### Purpose
**Attendance Settings** is a Single DocType (Global Configuration) that defines the rules of the game for the entire university.

### Key Configuration Points
*   **Thresholds**: Sets the `minimum_attendance_percentage` (e.g., 75%).
*   **Locking**: Defines `attendance_lock_days` to freeze old records (preventing retroactive tampering).
*   **Course Logic**: Defines default hours for Core vs Elective courses (`core_course_hours`, `elective_course_hours`), used in planning.
*   **Office Hours**: Toggles if Office Hours count towards attendance (`include_office_hours_in_attendance`) and sets their weight.
*   **Calculations**: Controls automation (`auto_calculate_summary`).

### Impact
Changing a value here immediately affects validation logic across the entire system. For example, disabling FA/MFA here will instantly block all new applications.

---

## 7. Attendance Summary

### Purpose
The **Attendance Summary** is the aggregated "Scorecard" for a student in a specific course. It is the destination where all daily attendance records are summed up.

### Key Features
*   **Real-Time Dashboard**: Shows Total Conducted, Total Attended, Condoned Hours, and Final Percentage.
*   **Eligibility Flag**: The critical `Eligible for Exam` (Yes/No) field is calculated here.
*   **Direct Link**: Acts as the pivot point between a Student and a Course Offering.

### Data Flow
It is updated automatically whenever:
1.  A new `Student Attendance` record is marked.
2.  A `Student Attendance Condonation` is approved.
3.  An FA/MFA override is applied.

---

## 8. Attendance Edit Log

### Purpose
The **Attendance Edit Log** provides a secure, tamper-evident audit trail for any changes made to attendance records after their initial creation.

### Key Features
*   **Forensics**: Records `Who` changed `What`, `When`, and `Why`.
*   **Field-Level Tracking**: Captures the "Old Value" (e.g., Absent) and "New Value" (e.g., Present).
*   **Reasoning**: Enforces that users verify *why* they are changing older records (e.g., "Correction of manual error").

### Use Case
If a student disputes their attendance, this log proves exactly when a record was changed and by whom.

---

## 9. Office Hours Session & Office Hours Attendance

### Purpose
These are specialized entities designed to handle the unique nature of Office Hours, which differ from scheduled lectures.
*   **Office Hours Session**: Defines a faculty member's open slot (e.g., "Prof. Smith, Fridays 2-4 PM").
*   **Office Hours Attendance**: Tracks the specific duration a student spent in that session.

### Distinction from Regular Attendance
*   **Duration-Based**: Unlike a lecture (fixed 1 hour credit), a student might visit office hours for 15 minutes or 2 hours. This DocType captures that specific `duration_hours`.
*   **Optionality**: Usually does not increase the "Total Conducted Classes" denominator, but adds to the "Attended" numerator (Bonus Time).

### Relationship
The system allows configuring whether these specialized records feed into the main `Student Attendance` table or are kept separate for analytics only.

---

## 10. Attendance Period

### Purpose
The **Attendance Period** defines the standard time slots for the university (e.g., "Period 1: 09:00 - 10:00").

### Usage
*   **Scheduling**: Simplifies data entry when creating timetables (select "Period 1" instead of typing start/end times manually).
*   **Validation**: Ensures `Attendance Sessions` align with approved university time blocks.

