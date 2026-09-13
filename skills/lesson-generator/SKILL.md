---
name: lesson-generator
description: Generate a structured lesson on a topic. Use when the user asks for a lesson, tutorial, study guide, or "teach me". Not for answering one-off factual questions or writing non-educational content.
---

# Lesson Generator

## Objective

Teach the user from first principles what they've asked about. Assume little to no knowledge in the subject area. 
Ground explanations in what the user is likely to know, you can ask them about their level of knowledge.

## Inputs

User provides a thing or list of things they want to learn about. They can also direct you to a learning roadmap if they have one.

## Steps

1. Generate an outline of a lesson plan 
2. Research and fill in details of each section, making sure to link everything together and gradually build up to more advanced concepts.
3. Create graphs, figures, and interactive elements (like sliders, visualized pipelines, etc.)

## Output format

- Lesson in a nice styled artifact (HTML/CSS/JS/TS) folder, clean and expressive.
- The lesson should be a folder with all files contained there, it should have a clear entry point (like lesson.hmtl).
- The lesson should use nice, modern styling. Reference 21st.dev and reactbits.dev for nice examples.
- The user should be able to open this lesson in any browser on any computer (goal is portability).
- At the user's request, the lesson can be generated with non-interactive elements and saved as a PDF.
