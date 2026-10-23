# Mistake-to-Mastery: A Neuro-Symbolic Tutor for Verified Misconception Diagnosis in Multilingual STEM Education

**Mistake-to-Mastery** is an AI-assisted tutoring research project that explores how students' procedural mistakes can be identified and explained using a combination of symbolic verification and large language models (LLMs).

The central design principle is **verify first, explain second**: where a problem can be checked formally, symbolic methods determine correctness, while language models support input extraction and explanations rather than making the grading decision.

> **Research status:** This repository accompanies an ongoing research project. Reported evaluation results are preliminary and should not be interpreted as evidence of improved learning outcomes or independently validated diagnostic performance.

## Research objectives

- Identify the first incorrect step in supported mathematical solutions.
- Match observed errors to a library of known misconception patterns.
- Separate correctness verification from natural-language explanation.
- Explore multilingual and multimodal interaction for STEM tutoring.
- Support targeted practice and spaced review based on learner history.

## How it works

The proposed system follows this workflow:

1. **Student input:** A learner submits a solution or problem.
2. **Input extraction:** An extraction component converts the submitted work into a structured representation.
3. **Symbolic verification:** Rule-based checks identify the first incorrect step in supported problem types.
4. **Misconception diagnosis:** An executable library compares the student's step with candidate error transformations.
5. **Explanation:** An explanation component communicates the verified error in accessible language.
6. **Practice and review:** The system can offer a related practice problem and track recurring errors where these features are implemented and enabled.

The symbolic verification component is designed to keep correctness decisions separate from LLM-generated explanations.

## Technologies

The research manuscript describes the following technologies and methods:

- **Python** — core implementation language
- **SymPy** — symbolic mathematics and equation verification
- **Pint** — unit-aware physical quantity checks
- **Streamlit** — user interface
- **SQLite** — learner and attempt data storage
- **Whisper** — speech-to-text processing
- **Large language models** — input extraction and natural-language explanations

The presence of a technology in this list describes the research design; it does not imply that every modality or feature has been fully validated.

## Supported research scope

The manuscript describes misconception rules for selected tasks involving:

- Algebraic sign errors and division mistakes
- Distribution errors
- Differentiation and integration
- Chemical equation balancing
- Physics unit and conversion errors

**Important limitation:** The reported synthetic evaluation covers four algebraic misconception rules only. Results should not be generalised to all subjects, languages, or input modalities.

## Preliminary evaluation

The current manuscript reports a synthetic evaluation of algebraic misconception diagnosis:

| Measure | Reported result |
|---|---:|
| Retained synthetic cases diagnosed | 387/387 |
| False alarms on correct synthetic solutions | 0/100 |
| Generated cases excluded because the transformation preserved the solution set | 13 |
| Exploratory user-feedback responses | 39 |

These results require careful interpretation. The synthetic cases were generated from the same misconception rules used by the diagnoser, so the evaluation does not establish independent diagnostic validity. The user-feedback survey is descriptive and does not establish learning gains.

Accuracy for photograph extraction, speech input, and multilingual extraction has not yet been established in the manuscript.

## Installation and usage

Installation instructions depend on the current state of the repository.

Before running the project, check whether the repository contains a dependency file such as `requirements.txt` and follow the setup instructions provided with the code. Do not assume that all external services or optional features are configured by default.

If you are a researcher or developer exploring this project, please verify the available modules, dependencies, configuration requirements, and implemented features in the source code before using it.

## Reproducibility

For reproducible evaluation, future releases should document:

- The exact code version used for each experiment
- The generation procedure and parameters for synthetic test cases
- The rules covered by each evaluation
- Exclusion criteria and false-positive handling
- Test commands and expected outputs
- Limitations and any changes to the evaluation protocol

Independent testing on student solutions not used to construct the misconception library is an important next step.

## Research paper

**Title:** *Mistake-to-Mastery: A Neuro-Symbolic Tutor for Verified Misconception Diagnosis in Multilingual STEM Education*

**Author:** Jana Amr

**Research affiliation stated in the manuscript:** Department of AI Engineering Research, K.R. Mangalam University

**Publication status:** Update this section once the paper's submission, acceptance, and publication status is confirmed. Do not describe the paper as published or accepted before formal confirmation.

## Limitations and future work

Future research should prioritise:

- Independent evaluation using authentic student solutions
- Measurement of input-extraction accuracy across languages and modalities
- Evaluation of unknown and unrecognised misconception cases
- Controlled classroom studies measuring learning outcomes
- Validation of explanations and multilingual output
- Reproducibility, privacy, and security testing

Mistake-to-Mastery is intended as a tutoring aid and research prototype, not a replacement for teachers or independent assessment.

## Contact

For research-related questions, please use the contact information provided in the associated research manuscript or contact the repository owner through GitHub.
