                  ┌─────────────────────────────┐
                         │       API / Chatbot         │
                         │   receives user request     │
                         └──────────────┬──────────────┘
                                        │
                                        v
                         ┌─────────────────────────────┐
                         │       SessionRuntime         │
                         │ load/save WMState           │
                         │ append user message         │
                         └──────────────┬──────────────┘
                                        │
                                        v
                         ┌─────────────────────────────┐
                         │       Parent LangGraph       │
                         │   owns durable WMState       │
                         └──────────────┬──────────────┘
                                        │
                                        v
                         ┌─────────────────────────────┐
                         │        Router Node           │
                         │  outputs RoutingDecision     │
                         └───────────┬─────────┬───────┘
                                     │         │
                            lookup   │         │ diagnose
                                     │         │
                                     v         v
                    ┌──────────────────────┐  ┌──────────────────────┐
                    │     Lookup Flow      │  │   Diagnosis Flow     │
                    │ reads WMState        │  │ reads WMState        │
                    │ may call SQL tool    │  │ may call SQL tool    │
                    └──────────┬───────────┘  └──────────┬───────────┘
                               │                         │
                               │ tool call               │ tool call
                               └──────────────┬──────────┘
                                              v
                          ┌────────────────────────────────────┐
                          │         SQL TOOL ADAPTER           │
                          │ converts WMState -> SQLGraphState  │
                          │ invokes SQL subgraph sequentially  │
                          └──────────────────┬─────────────────┘
                                             v
                    ┌───────────────────────────────────────────────────┐
                    │              SQL SUBGRAPH (sequential)            │
                    │            owns local SQLGraphState only          │
                    ├───────────────────────────────────────────────────┤
                    │ 1. understand sql intent                          │
                    │ 2. fetch schema/context                           │
                    │ 3. generate SQL                                   │
                    │ 4. validate / repair SQL                          │
                    │ 5. execute query                                  │
                    │ 6. summarize result                               │
                    └──────────────────┬────────────────────────────────┘
                                       │
                                       v
                         ┌─────────────────────────────┐
                         │      SQLTaskResult          │
                         │ typed result contract       │
                         │ rows / sql / summary / err  │
                         └──────────────┬──────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     │                                     │
                     v                                     v
          ┌──────────────────────────┐         ┌──────────────────────────┐
          │ Lookup Flow updates      │         │ Diagnosis Flow updates   │
          │ lookup_result            │         │ diagnosis_result         │
          │ maybe draft response     │         │ maybe draft response     │
          └──────────────┬───────────┘         └──────────────┬───────────┘
                         └──────────────────┬──────────────────┘
                                            v
                         ┌─────────────────────────────┐
                         │   Parent Graph Finalizer    │
                         │ writes final_response       │
                         │ updates WMState             │
                         └──────────────┬──────────────┘
                                        │
                                        v
                         ┌─────────────────────────────┐
                         │       SessionRuntime        │
                         │ persist updated WMState     │
                         └──────────────┬──────────────┘
                                        │
                                        v
                         ┌─────────────────────────────┐
                         │       API response          │
                         └─────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                        STATE FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    WMState (Durable)                        │ │
│  │  - Long-lived state owned by Parent LangGraph               │ │
│  │  - Persisted to database by Session Runtime                 │ │
│  │  - Contains inventory, locations, orders, issues            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  SQLGraphState (Temporary)                 │ │
│  │  - Schema information                                       │ │
│  │  - Generated/validated SQL                                   │ │
│  │  - Query results                                             │ │
│  │  - Passed through SQL Tool Adapter → SQL Subgraph           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  RoutingDecision (Temporary)               │ │
│  │  - User Intent Detection (lookup vs diagnosis)              │ │
│  │  - Passed to Router Node                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Flow Results (Temporary)                  │ │
│  │  - lookup_result OR diagnosis_result                        │ │
│  │  - Finalized by Parent Graph Finalizer                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

User Request → API Chatbot → Session Runtime (Load WMState)
              ↓
         Parent LangGraph
              ↓
           Router Node
              ↓
      ┌───────┴───────┐
      ↓               ↓
 Lookup Flow   Diagnosis Flow
      ↓               ↓
    SQL Tool    SQL Tool
      ↓               ↓
 SQL Subgraph (Sequential)
      ↓
   SQL Task Result
      ↓
 Parent Finalizer
      ↓
  Session Runtime (Persist)
      ↓
   API Response → User