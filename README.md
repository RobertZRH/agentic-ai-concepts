# Agentic AI Concepts

A repository exploring agentic AI concepts and implementations.

## What is Agentic AI?

Agentic AI refers to AI systems that can autonomously plan, reason, and take actions to achieve goals — going beyond simple question-answering to executing multi-step tasks with minimal human intervention.

## Core Concepts

### 1. Agents
An **agent** is an AI system that perceives its environment, makes decisions, and takes actions to reach a goal. Agents can use tools, call APIs, browse the web, write code, and more.

### 2. Planning
Agents break down complex goals into smaller sub-tasks. Common planning strategies include:
- **ReAct** (Reason + Act): Interleave reasoning steps with tool calls
- **Chain-of-Thought**: Step-by-step reasoning before acting
- **Tree of Thoughts**: Explore multiple reasoning paths in parallel

### 3. Memory
Agents use different types of memory to maintain context:
- **Short-term (in-context)**: Information within the current conversation window
- **Long-term (external)**: Databases, vector stores, or files persisted across sessions
- **Episodic**: Recalled past interactions to inform current behavior

### 4. Tools & Actions
Agents are equipped with tools to interact with the world:
- Web search
- Code execution
- File read/write
- API calls
- Database queries

### 5. Orchestration
Multi-agent systems use an **orchestrator** to coordinate multiple specialized agents working in parallel or in sequence toward a shared goal.

### 6. Feedback Loops
Agents evaluate their own output and iterate:
- **Self-reflection**: Critique and revise responses
- **Human-in-the-loop**: Pause for human approval at key decision points
- **Automated evaluation**: Use metrics or another model to score results

## Agentic Process Flow

```
Goal → Plan → Act (Tool Use) → Observe → Reflect → Repeat → Done
```

## Key Frameworks

| Framework | Description |
|-----------|-------------|
| LangChain / LangGraph | Python framework for building agentic pipelines |
| AutoGen | Multi-agent conversation framework by Microsoft |
| Semantic Kernel | SDK for integrating AI into applications (.NET, Python) |
| CrewAI | Role-based multi-agent orchestration |
| Azure AI Agent Service | Managed agentic AI on Azure |
