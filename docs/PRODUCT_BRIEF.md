# Product Brief

## Product

AgentOS Lite: Self-hosted AI Workspace with RAG, Memory, Tools, Approvals, LLMOps, and Codebase Intelligence.

## Target User

Developers and AI builders who want a local, explainable agent workspace they can run, inspect, and extend.

## Problem

AI assistants often answer without evidence, forget user/project context, call tools without enough control, and hide model/retrieval behavior.

## Solution

AgentOS Lite creates a local agent operating loop:

- Documents provide citation-backed RAG context.
- Memory stores durable user preferences and project context.
- Codebase intelligence indexes repositories and explains relevant files.
- Tools execute safe actions and pause risky actions for approval.
- LLMOps records model calls, retrievals, traces, errors, and fallback behavior.

## Core Flow

Ask a question, retrieve context, plan the run, use tools safely, approve risky work, and inspect the final answer with citations and logs.

## MVP Boundaries

The MVP uses SQLite, deterministic mock models, mock embeddings, a default local user, and optional Gemini. It does not claim production hosting, auth, vector database search, or unrestricted real-model usage.
