#!/usr/bin/env python

import os
import csv
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")


async def import_faqs_from_csv(csv_file_path):
    """
    Import FAQs from a CSV file and add them to the database via API
    """
    print(f"Importing FAQs from {csv_file_path}...")

    # Read CSV file
    faqs = []
    with open(csv_file_path, "r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            faqs.append({"question": row["Question"], "answer": row["Answer"]})

    print(f"Found {len(faqs)} FAQs in the CSV file.")

    # Add FAQs to database via API
    async with aiohttp.ClientSession() as session:
        for faq in faqs:
            try:
                # Check if FAQ already exists (simple check by question text)
                async with session.get(f"{API_BASE_URL}/private/faq") as response:
                    if response.status == 200:
                        existing_faqs = await response.json()
                        # Check if question already exists
                        if any(
                            existing["question"] == faq["question"]
                            for existing in existing_faqs
                        ):
                            print(f"FAQ already exists: {faq['question'][:50]}...")
                            continue

                # Add new FAQ
                async with session.post(
                    f"{API_BASE_URL}/private/faq", json=faq
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        print(f"Added FAQ: {result['question'][:50]}...")
                    else:
                        error = await response.text()
                        print(f"Error adding FAQ: {error}")
            except Exception as e:
                print(f"Error processing FAQ: {e}")

    print("FAQ import completed!")


async def main():
    """Main function"""
    # Path to the CSV file
    csv_file_path = os.path.join(os.path.dirname(__file__), "gameshop_faq.csv")

    # Import FAQs
    await import_faqs_from_csv(csv_file_path)


if __name__ == "__main__":
    asyncio.run(main())
