"""Synthetic student data generator for testing and modeling without PII."""

import random

import pandas as pd


def generate_synthetic_students(num_students=100):
    """Generate a DataFrame of synthetic student records."""
    first_names = ["Ayesha", "Rahim", "Sumon", "Mitu", "Jamal", "Rina"]
    last_names = ["Islam", "Hossain", "Khan", "Akter", "Mia", "Begum"]
    divisions = ["Dhaka", "Chittagong", "Khulna", "Rajshahi", "Barisal", "Sylhet"]
    data = []
    for _ in range(num_students):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"  # nosec
        student_id = f"S{random.randint(10000, 99999)}"  # nosec
        division = random.choice(divisions)  # nosec
        gpa = round(random.uniform(2.0, 5.0), 2)  # nosec
        data.append({"student_id": student_id, "name": name, "division": division, "gpa": gpa})
    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_synthetic_students(10)
    print(df)
