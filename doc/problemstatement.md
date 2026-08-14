# Problem Statement: AI-Powered Restaurant Recommendation System

**Use case:** Zomato

## Overview

Build an AI-powered restaurant recommendation service inspired by Zomato. The system should suggest restaurants based on user preferences by combining structured restaurant data with a Large Language Model (LLM).

## Objective

Design and implement an application that:

- Accepts user preferences such as location, budget, cuisine, and ratings
- Uses a real-world restaurant dataset
- Leverages an LLM to generate personalized, human-like recommendations
- Presents clear, useful results to the user

## System Workflow

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:  
  [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Extract relevant fields such as restaurant name, location, cuisine, cost, and rating

### 2. User Input

Collect the following preferences:

| Preference | Examples |
| --- | --- |
| Location | Delhi, Bangalore |
| Budget | Low, medium, high |
| Cuisine | Italian, Chinese |
| Minimum rating | e.g., 4.0+ |
| Additional preferences | Family-friendly, quick service |

### 3. Integration Layer

- Filter and prepare restaurant data based on user input
- Pass the structured results into an LLM prompt
- Design a prompt that helps the LLM reason about and rank options

### 4. Recommendation Engine

Use the LLM to:

- Rank restaurants
- Explain why each recommendation fits the user’s preferences
- Optionally summarize the overall choices

### 5. Output Display

Present the top recommendations in a user-friendly format, including:

- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation
