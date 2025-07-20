import random
import string
import json
from datetime import datetime


# Helper function to generate alphanumeric IDs
def generate_alphanumeric_id(prefix, length=6):
    """Generate an alphanumeric ID with a prefix (e.g., 'PAT' or 'DOC')."""
    chars = string.ascii_uppercase + string.digits  # A-Z + 0-9
    random_part = ''.join(random.choice(chars) for _ in range(length))
    return f"{prefix}-{random_part}"


class Person:
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender

    def display_details(self):
        return f"Name: {self.name}, Age: {self.age}, Gender: {self.gender}"


class Patient(Person):
    def __init__(self, name, age, gender):
        super().__init__(name, age, gender)
        self.patient_id = generate_alphanumeric_id("PAT")
        self.appointment_list = []

    def view_profile(self):
        appointments = "\n".join([f" - {a.appointment_id} ({a.date} {a.time})"
                                  for a in self.appointment_list])
        return (f"Patient ID: {self.patient_id}\n"
                f"{super().display_details()}\n"
                f"Appointments:\n{appointments or 'None'}")


class Doctor(Person):
    def __init__(self, name, age, gender, specialty):
        super().__init__(name, age, gender)
        self.doctor_id = generate_alphanumeric_id("DOC")
        self.specialty = specialty
        self.schedule = []

    def is_available(self, date_time):
        return date_time not in self.schedule

    def view_schedule(self):
        return (f"Doctor ID: {self.doctor_id}\n"
                f"Specialty: {self.specialty}\n"
                f"Available Slots:\n - " + "\n - ".join(self.schedule) if self.schedule else "No available slots")


class Appointment:
    def __init__(self, patient, doctor, date, time):
        self.appointment_id = generate_alphanumeric_id("APT")
        self.patient = patient
        self.doctor = doctor
        self.date = date
        self.time = time
        self.status = "Scheduled"
        patient.appointment_list.append(self)

    def confirm(self):
        self.status = "Confirmed"
        return f"Appointment {self.appointment_id} confirmed."

    def cancel(self):
        self.status = "Cancelled"
        self.doctor.schedule.remove(f"{self.date} {self.time}")
        return f"Appointment {self.appointment_id} cancelled."


class HospitalSystem:
    def __init__(self):
        self.patients = []
        self.doctors = []
        self.appointments = []
        self.load_data()

    def save_data(self):
        data = {
            "patients": [vars(p) for p in self.patients],
            "doctors": [vars(d) for d in self.doctors],
            "appointments": [{
                "appointment_id": a.appointment_id,
                "patient_id": a.patient.patient_id,
                "doctor_id": a.doctor.doctor_id,
                "date": a.date,
                "time": a.time,
                "status": a.status
            } for a in self.appointments]
        }
        with open("hospital_data.json", "w") as f:
            json.dump(data, f, indent=2)

    def load_data(self):
        try:
            with open("hospital_data.json", "r") as f:
                data = json.load(f)

                # Recreate patients
                self.patients = []
                for p_data in data["patients"]:
                    patient = Patient(p_data["name"], p_data["age"], p_data["gender"])
                    patient.patient_id = p_data["patient_id"]
                    self.patients.append(patient)

                # Recreate doctors
                self.doctors = []
                for d_data in data["doctors"]:
                    doctor = Doctor(d_data["name"], d_data["age"], d_data["gender"], d_data["specialty"])
                    doctor.doctor_id = d_data["doctor_id"]
                    doctor.schedule = d_data["schedule"]
                    self.doctors.append(doctor)

                # Recreate appointments
                self.appointments = []
                for a_data in data["appointments"]:
                    patient = next(p for p in self.patients if p.patient_id == a_data["patient_id"])
                    doctor = next(d for d in self.doctors if d.doctor_id == a_data["doctor_id"])
                    appointment = Appointment(patient, doctor, a_data["date"], a_data["time"])
                    appointment.appointment_id = a_data["appointment_id"]
                    appointment.status = a_data["status"]
                    self.appointments.append(appointment)

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # Initialize with sample data if file doesn't exist or is corrupted
            self.patients = []
            self.doctors = []
            self.appointments = []

    def add_patient(self, name, age, gender):
        patient = Patient(name, age, gender)
        self.patients.append(patient)
        self.save_data()
        return patient

    def add_doctor(self, name, age, gender, specialty):
        doctor = Doctor(name, age, gender, specialty)
        self.doctors.append(doctor)
        self.save_data()
        return doctor

    def book_appointment(self, patient_id, doctor_id, date, time):
        patient = next((p for p in self.patients if p.patient_id == patient_id), None)
        doctor = next((d for d in self.doctors if d.doctor_id == doctor_id), None)

        if not patient:
            raise ValueError("Patient not found.")
        if not doctor:
            raise ValueError("Doctor not found.")

        date_time = f"{date} {time}"
        if not doctor.is_available(date_time):
            raise ValueError("Doctor not available at this time.")

        appointment = Appointment(patient, doctor, date, time)
        doctor.schedule.append(date_time)
        self.appointments.append(appointment)
        self.save_data()
        return appointment

    def cancel_appointment(self, appointment_id):
        appointment = next((a for a in self.appointments if a.appointment_id == appointment_id), None)
        if not appointment:
            raise ValueError("Appointment not found.")
        return appointment.cancel()

    def generate_bill(self, appointment_id, additional_fees=0):
        """Generates a bill for the given appointment, including consultation fee and additional fees."""
        appointment = next((a for a in self.appointments if a.appointment_id == appointment_id), None)
        if not appointment:
            raise ValueError("Appointment not found.")

        consultation_fee = 3000  # JMD
        total = consultation_fee + additional_fees

        # Prepare the receipt with all services used
        receipt = (
            f"\n=== HEALTHCARE HOSPITAL ===\n"
            f"Appointment ID: {appointment.appointment_id}\n"
            f"Patient: {appointment.patient.name} ({appointment.patient.patient_id})\n"
            f"Doctor: {appointment.doctor.name} ({appointment.doctor.doctor_id})\n"
            f"Date: {appointment.date} {appointment.time}\n"
            f"----------------------------------\n"
            f"Consultation Fee: JMD {consultation_fee}\n"
        )

        # If there are additional services, print them out as well
        if additional_fees > 0:
            receipt += f"Additional Service Fees: JMD {additional_fees}\n"

        receipt += (
            f"----------------------------------\n"
            f"TOTAL: JMD {total}\n"
            f"----------------------------------\n"
        )

        return receipt

    def list_patients(self):
        return "\n".join([f"{p.patient_id}: {p.name}" for p in self.patients])

    def list_doctors(self):
        return "\n".join([f"{d.doctor_id}: {d.name} ({d.specialty})" for d in self.doctors])

    def list_appointments(self):
        return "\n".join(
            [f"{a.appointment_id}: {a.patient.name} -> {a.doctor.name} on {a.date} at {a.time} ({a.status})"
             for a in self.appointments])


def display_menu():
    print("\n===== HOSPITAL MANAGEMENT SYSTEM =====")
    print("1. Register Patient")
    print("2. Register Doctor")
    print("3. Book Appointment")
    print("4. View Patient Profile")
    print("5. View Doctor Schedule")
    print("6. Generate Bill")
    print("7. Cancel Appointment")
    print("8. List All Patients")
    print("9. List All Doctors")
    print("10. List All Appointments")
    print("11. Exit")


def get_valid_input(prompt, input_type=str):
    while True:
        try:
            value = input_type(input(prompt))
            return value
        except ValueError:
            print(f"Invalid input. Please enter a valid {input_type.__name__}.")


def main():
    hospital = HospitalSystem()

    # Initialize with sample data if empty
    if not hospital.patients:
        hospital.add_patient("John Doe", 30, "Male")
        hospital.add_patient("Jane Smith", 25, "Female")

    if not hospital.doctors:
        hospital.add_doctor("Dr. Williams", 45, "Male", "Cardiology")
        hospital.add_doctor("Dr. Johnson", 40, "Female", "Pediatrics")

    while True:
        display_menu()
        choice = input("Enter your choice (1-11): ")

        try:
            if choice == "1":
                print("\nRegister New Patient")
                name = input("Name: ")
                age = get_valid_input("Age: ", int)
                gender = input("Gender: ")
                patient = hospital.add_patient(name, age, gender)
                print(f"\nPatient registered successfully!\n{patient.view_profile()}")

            elif choice == "2":
                print("\nRegister New Doctor")
                name = input("Name: ")
                age = get_valid_input("Age: ", int)
                gender = input("Gender: ")
                specialty = input("Specialty: ")
                doctor = hospital.add_doctor(name, age, gender, specialty)
                print(f"\nDoctor registered successfully!\n{doctor.view_schedule()}")

            elif choice == "3":
                print("\nBook Appointment")
                print("\nAvailable Patients:")
                print(hospital.list_patients())
                patient_id = input("\nEnter Patient ID: ")

                print("\nAvailable Doctors:")
                print(hospital.list_doctors())
                doctor_id = input("\nEnter Doctor ID: ")

                date = input("Date (YYYY-MM-DD): ")
                time = input("Time (HH:MM): ")

                appointment = hospital.book_appointment(patient_id, doctor_id, date, time)
                print(f"\nAppointment booked successfully!\n"
                      f"Appointment ID: {appointment.appointment_id}\n"
                      f"Patient: {appointment.patient.name}\n"
                      f"Doctor: {appointment.doctor.name}\n"
                      f"Date: {appointment.date} at {appointment.time}")

            elif choice == "4":
                print("\nView Patient Profile")
                print(hospital.list_patients())
                patient_id = input("\nEnter Patient ID: ")
                patient = next((p for p in hospital.patients if p.patient_id == patient_id), None)
                if patient:
                    print(f"\n{patient.view_profile()}")
                else:
                    print("Patient not found.")

            elif choice == "5":
                print("\nView Doctor Schedule")
                print(hospital.list_doctors())
                doctor_id = input("\nEnter Doctor ID: ")
                doctor = next((d for d in hospital.doctors if d.doctor_id == doctor_id), None)
                if doctor:
                    print(f"\n{doctor.view_schedule()}")
                else:
                    print("Doctor not found.")

            elif choice == "6":
                print("\nGenerate Bill")
                print(hospital.list_appointments())
                appointment_id = input("\nEnter Appointment ID: ")
                additional_fees = get_valid_input("Enter Additional Service Fees (JMD): ", float)
                print(hospital.generate_bill(appointment_id, additional_fees))

            elif choice == "7":
                print("\nCancel Appointment")
                print(hospital.list_appointments())
                appointment_id = input("\nEnter Appointment ID to cancel: ")
                result = hospital.cancel_appointment(appointment_id)
                print(f"\n{result}")

            elif choice == "8":
                print("\nList of All Patients:")
                print(hospital.list_patients())

            elif choice == "9":
                print("\nList of All Doctors:")
                print(hospital.list_doctors())

            elif choice == "10":
                print("\nList of All Appointments:")
                print(hospital.list_appointments())

            elif choice == "11":
                print("\nExiting system. Goodbye!")
                break

            else:
                print("\nInvalid choice. Please try again.")

        except ValueError as e:
            print(f"\nError: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
