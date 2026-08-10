# inventory-research

This repository contains the implementation of a comprehensive inventory management model that synthesizes classical economic order quantity (EOQ) formulations with carbon emissions regulations, backlogs, green technology investments, and power demand patterns.

The primary goal is to reproduce and unify several key operations research baselines from the literature, and subsequently extend them into novel multi-policy frameworks (Phase 3a, 3b, 3c).

## Table of Contents
- [Features and Models](#features-and-models)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Testing](#testing)
- [License](#license)

## Features and Models

The project structure is divided into **baselines** (reproducing existing literature) and **novel models** (synthesizing and extending baselines).

### Literature Baselines
The codebase accurately implements models from foundational research:
- **Hua et al. (2011)**: EOQ under cap-and-trade carbon policies.
- **Benjaafar et al. (2013)**: Lot-sizing under multiple carbon policies (strict cap, tax, cap-and-offset).
- **Sicilia et al. (2014)**: Inventory models with power demand patterns and shortages/backlogs.
- **Hasan et al. (2021)**: Green technology investments and demand-coupling effects.

### Novel Extensions (Phase 3)
- **Phase 3a (Power Demand + Cap-and-Trade)**: Combines Sicilia's (2014) power-demand structure with Hua's (2011) cap-and-trade emissions accounting.
- **Phase 3b (Green Technology)**: Layers Hasan's (2021) green-tech investment $G$ onto the Phase 3a backbone, enabling closed-form optimization and univariate search.
- **Phase 3c (Multi-Policy Framework)**: Unified solver interface comparing carbon taxes, cap-and-trade, and strict-cap policies seamlessly.

## Project Structure

```text
.
├── analysis/           # Scripts to run sensitivity sweeps (G1-G5) and generate results
├── docs/               # Detailed documentation, notation cross-references, and proofs
├── papers/             # Reference literature (PDFs)
├── src/                # Core implementation
│   ├── baselines/      # Reproductions of Hua, Benjaafar, Sicilia, Hasan
│   └── novel/          # Novel integrated models (Phase 3a, 3b, 3c)
├── tests/              # Extensive pytest suite (400+ tests validating numerical properties)
└── requirements.txt    # Python dependencies
```

## Installation

The project requires Python 3.9+ (Python 3.12+ recommended). Install the required dependencies using `pip`:

```bash
git clone https://github.com/yourusername/inventory-research.git
cd inventory-research
pip install -r requirements.txt
```

## Usage

### Running Sensitivity Analyses
The `analysis` directory contains sweeps corresponding to different research gaps (G1 to G5). Each script emits a CSV, a publication-ready PDF figure, and findings. To run them:

```bash
# Example: Run the Gap 1 sensitivity sweep (varying the power-demand exponent)
python -m analysis.sweep_g1
```

### Python API
You can also use the models directly from Python. For example, to run the Phase 3c multi-policy comparison:

```python
from src.novel.stage_3c_multipolicy import compare_policies

results = compare_policies(
    D=300, n=2, alpha=1.5, h=0.05, s=0.10, K=20,
    e_K=20, e_h=1, a=3.0, b=0.5, p_c=0.5, C_cap=10.0
)

print(results["cap_and_trade"]["cost"])
```

## Documentation

Extensive documentation is provided in the `docs/` directory:
- **`docs/notation.md`**: An authoritative, unified symbol table mapping paper-specific notations to a single standard API.
- **`docs/plan.md`**: Implementation roadmap, sprint phases, and key takeaways for every milestone.
- **`docs/proofs.md`**: Formalizes the mathematical propositions underlying the novel solvers.

## Testing

The project has rigorous test coverage (>400 tests), verifying optimal-cost identities, Lagrangian equivalence, monotonicity, and exact numerical reproduction of tables from the original papers.

Run the test suite using `pytest`:

```bash
pytest
```

## License

This project is licensed under the terms specified in the `LICENSE` file.
