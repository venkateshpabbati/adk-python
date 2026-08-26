# ADK Developer Guides

These are the reference guides for the ADK Python implementation, with one page
per unit. Tutorials, conceptual overviews and the released API reference live
at [adk.dev](https://adk.dev/).

## Start here

Read these seven pages in order. They cover an agent that answers a user, calls
your code, and remembers what happened afterwards, and each one uses something
the page before it introduced.

1. **[LlmAgent Chat Mode](agents/llm_agent/chat.md)** is the agent itself. Chat
   is the default mode, so an `LlmAgent(...)` written with no `mode` set is a
   chat agent.
2. **[App](apps/app/index.md)** is the container you put the agent in. The
   runner in step 3 takes an `App`, and every application-wide setting later in
   this list is attached here.
3. **[Runner and InMemoryRunner](runners/runner/index.md)** is the object you
   actually call. It loads or creates the session, runs the agent, and streams
   the results back. `InMemoryRunner` needs no storage to set up, so the steps
   up to here run without you choosing a backend.
4. **[Event](events/event/index.md)** is what the runner streams back. Every
   model reply, function call and state change arrives as an `Event`, so you
   cannot read your agent's output until you can read one.
5. **[FunctionTool](tools/function_tool/index.md)** is how a plain Python
   function becomes something the model can call. A call to one, and the value
   it returns, both reach you as events from step 4. Read it before writing any
   tool, because ADK infers the tool's declaration from your signature and
   docstring, and that inference can be wrong.
6. **[State](sessions/state/index.md)** explains how a value written on one turn
   is still there on the next. A tool from step 5 writes here when it has
   something to remember between calls. The `app:`, `user:` and `temp:` prefixes
   decide how far a value travels and whether it is stored at all.
7. **[Session and BaseSessionService](sessions/session/index.md)** covers what a
   conversation record holds, and the interface behind every storage backend.
   The state from step 6 lives in a session, which is what a backend has to
   store for a value to survive a restart. Read it when in-memory sessions stop
   being enough.

### Where to go next

- If your agent needs to survive a restart, pick a
  [session backend](#session-backends), then add [memory](#memory) when it
  should also recall earlier conversations.
- When the order of steps should be yours and not the model's, read
  [Workflows](#workflows).
- When your agent needs to reach a real system, go to [Tools](#tools), which
  covers writing your own, generating them from an OpenAPI or Google API spec,
  and the cloud toolsets ADK ships.
- To find out whether a change made the agent better, read
  [Evaluation and optimization](#evaluation-and-optimization).

## Every guide by area

Eight areas hold all 100 guides. A guide for a specific cloud or third-party
product sits next to the ADK interface it implements, so `RedisSessionService`
is under sessions and `BigQueryToolset` is under tools rather than in a
separate integrations bucket.

- [Agents and models](#agents-and-models) covers the agent classes, what shapes
  their behavior, and the model layer underneath.
- [Tools](#tools) covers writing tools, the tools ADK ships, credentials, code
  execution, and cloud toolsets.
- [Workflows](#workflows) is for running a graph of nodes instead of letting a
  model choose the order.
- [Running an app](#run-an-app) covers the runner, the event stream, live
  audio, HTTP serving, and diagnosing failures.
- [Sessions, state, memory and artifacts](#sessions-state-memory-and-artifacts)
  holds everything that outlives a single model call.
- [Remote agents, A2A and MCP](#remote-agents-a2a-and-mcp) is about exposing
  your agent to others and calling agents that run elsewhere.
- [Plugins and skills](#plugins-and-skills) covers behavior that applies to a
  whole app, and instructions an agent loads on demand.
- [Evaluation and optimization](#evaluation-and-optimization) is where you
  score agent quality and rewrite instructions from the scores.

## Agents and models

An agent pairs a model with an instruction and a set of tools. The class you
choose decides when the agent stops and who it hands control back to, which is
the decision the rest of the settings sit on top of.

### Agent classes

* [LlmAgent Chat Mode](agents/llm_agent/chat.md) is the default conversational agent, and what you get when you write `LlmAgent(...)` with no `mode` set. It holds the conversation, keeps the history, and transfers to a peer or parent agent when someone else should answer.
* [LlmAgent Task Mode](agents/llm_agent/task.md) is an agent you hand a goal to and then let run its own loop, until it calls the built-in `finish_task` tool. The arguments it passes to that tool are checked against your output schema.
* [LlmAgent Single-Turn Mode](agents/llm_agent/single_turn.md) runs the agent once and keeps no state, which suits a step in a workflow graph or a specialist a parent agent calls like a function, because neither carries a conversation forward. Single-turn mode is what replaced `AgentTool`.
* [BaseAgent](agents/base_agent/index.md) is the class every agent inherits from, and the one you subclass when a step is plain Python instead of a model call. It also owns `before_agent_callback` and `after_agent_callback`, which work on any agent, including one you did not write.
* [ManagedAgent](agents/managed_agent/index.md) drives an agent that Google hosts and runs for you. Its model loop, sandbox and tools all stay server-side, and locally you keep only the two ids that resume the remote conversation.
* [Agent config (YAML)](agents/agent_config/index.md) lets you declare an agent tree in `root_agent.yaml` instead of Python. It covers the schema, where `adk web` and `adk run` look for the file, and how that file references tools, sub-agents and custom classes.

### Shape what an agent does

* [Context](agents/context/index.md) is the object handed to every callback, tool and workflow node. Read it to see how any of them reaches session state, artifacts, memory, credentials and tool confirmation.
* [RunConfig](agents/run_config/index.md) holds the per-invocation settings you pass to `run_async`, including token-by-token streaming, a cap on model calls, billing labels, and the live audio configuration.
* [inject_session_state](utils/instructions_utils/index.md) is the template engine behind `{var}`, `{var?}` and `{artifact.name}` in an instruction string. You call it yourself when you write an instruction as a callable.
* [McpInstructionProvider](agents/mcp_instruction_provider/index.md) fetches an agent's instruction from an MCP server prompt on every request. If that prompt takes arguments, it fills them from session state by matching names.
* [Example and ExampleTool](examples/example/index.md) covers few-shot prompting. `ExampleTool` is the only thing that gets your input and output pairs in front of the model, either from a fixed list or from a provider that picks them per query.
* [BasePlanner](planners/planner/index.md) makes the model plan before it acts. It injects planning instructions, sets a thinking configuration, and splits a reply into its reasoning, its tool calls and its final answer. `PlanReActPlanner` drives that split with Plan-Re-Act prompt tags on any model.

### Models

* [BaseLlm and LLMRegistry](models/llm_registry/index.md) describes the interface every model implementation satisfies, how the model-name string on an agent resolves to a class, and how you register your own.
* [Gemini](models/google_llm/index.md) is the model class an agent gets by default. Read it when a model name string is not enough and you need to control the client, the API version, retries, or the project and location.
* [LiteLlm](models/lite_llm/index.md) runs an agent on OpenAI, Anthropic, Ollama, Bedrock, Azure, Mistral or any other provider LiteLLM supports, and it explains what ADK does with the keyword arguments you forward.
* [LlmRequest and LlmResponse](models/llm_request_response/index.md) are the two objects every model callback and model-facing plugin hook receives. Read this before you try to inspect or rewrite what passes between an agent and its model.
* [ContextCacheConfig](agents/context_cache_config/index.md) turns on Gemini explicit context caching for a whole `App`. Setting it is necessary and not sufficient, because several conditions decide whether a cache is created, and nothing is reported when they fail.
* [CacheMetadata](models/cache_metadata/index.md) tells you whether a context cache is actually working. It is the record ADK attaches to each response, and you can read it live in a callback or afterwards from the session.

## Tools

A tool is a function the model can choose to call, and ADK sends the model a
declaration of each one so that it knows what is available. You can write a
tool yourself, generate a set of them from an API description, or use the ones
ADK ships.

### Write your own tool

* [FunctionTool](tools/function_tool/index.md) turns a plain Python function into a tool. It covers what ADK infers from the signature and docstring, and what to do when that inference is wrong.
* [ToolContext](tools/tool_context/index.md) is the extra argument a tool can declare. If your function takes one, it can reach session state, artifacts, memory, credentials, confirmation, and the actions that change what the agent does next. It is an alias of [`Context`](agents/context/index.md).
* [BaseTool](tools/base_tool/index.md) is the two-method subclassing contract you implement when a plain function cannot express the tool, including one whose only job is to shape the outgoing request.
* [BaseToolset and ToolPredicate](tools/base_toolset/index.md) let you decide a group of tools at run time instead of import time. The page also covers `tool_filter` and `tool_name_prefix`, the two knobs every prebuilt ADK toolset inherits from it.
* [LongRunningFunctionTool](tools/long_running_tool/index.md) is for tools whose real result arrives on a later turn, after a batch job, an approval or a webhook. Your application has to implement the resuming half itself.
* [A workflow node as a tool](tools/node_tool/index.md) puts a `Workflow` or a `@node` function directly in `LlmAgent.tools`, so the call can emit events while it runs and can pause mid-call to ask a human something.
* [AgentTool](tools/agent_tool/index.md) wraps an agent as a tool. It is still supported, though its own docstring discourages it, because a single-turn sub-agent delegates the same work without running the sub-agent in a session of its own. Read the page to compare the two before choosing.

### Tools ADK gives you

* [Built-in Gemini tools](tools/builtin_gemini_tools/index.md) covers six capabilities the model can use directly: Google Search, URL fetching, enterprise web search, Maps grounding, and two routes into a Vertex AI Search data store. Five of them run inside the model, and the sixth is an ordinary local tool. An agent generally gets one built-in at a time, and the page gives you the way around that.
* [Retrieval tools](tools/retrieval/index.md) give the model a single `query` function over a document collection. You choose between a managed Vertex AI RAG corpus, a local directory, and a LlamaIndex retriever you already have.
* [OpenAPIToolset and RestApiTool](tools/openapi_tool/openapi_toolset/index.md) turn an OpenAPI 3 document into one tool per operation. The page covers the snake-case renaming of operation ids and the auth handshake that goes with it.
* [GoogleApiToolset](tools/google_api_tool/google_api_toolset/index.md) gives you Calendar, Gmail, Sheets, Slides, Docs, YouTube and BigQuery as ready-made toolsets, any other Google API by name, and a way to cut the generated list down to the few tools an agent should actually see.
* [SkillToolset](tools/skill_toolset/index.md) gives an agent a library of [skills](#skills) that it discovers by name and loads only when it needs them. Loading one adds instructions, and can add tools, in the middle of a turn.
* [BaseComputer](tools/computer_use/base_computer/index.md) is the sixteen-method interface a computer-use model drives. Your docstrings become the tool descriptions the model reads, so writing them is part of writing the implementation.
* [Built-in utility tools](tools/builtin_utility_tools/index.md) are the ten small tools ADK ships, among them exiting a loop, fetching a web page, asking the user to choose, and the memory and artifact tools the model can call for itself.

### Approval and credentials

* [ToolConfirmation](tools/tool_confirmation/index.md) requires a human to approve a tool call before it runs, and covers the request-and-resume round trip around it. The answer can carry data with it, so it is not limited to yes or no.
* [AuthConfig and authenticated tools](auth/tool_auth/index.md) is where you declare the credential a tool needs, so that ADK pauses the run to collect it and then resumes the same call. Start here for anything OAuth-shaped.
* [BaseCredentialService](auth/credential_service/index.md) decides where a consented credential lives between turns, so the user is not asked for it again. It covers the two stores ADK ships and how to write your own.
* [BaseAuthProvider](auth/base_auth_provider/index.md) teaches ADK an authentication scheme it does not ship, and explains why a custom scheme does not get credential caching.

### Run code, shells and files

* [BaseCodeExecutor](code_executors/code_executor/index.md) lets the model write and run code. Seven backends implement it: a local subprocess with no isolation at all, containers under Docker or GKE with gVisor, the managed Vertex AI, Agent Engine and Cloud Run options, and Gemini's own server-side execution. The page compares them so you can pick one.
* [BaseEnvironment and LocalEnvironment](environment/base_environment/index.md) is the four-method interface behind "a place the agent can run shell commands and keep files", together with the implementation that uses subprocesses on your own host.
* [EnvironmentToolset](tools/environment/environment_toolset/index.md) puts four tools over a single environment: `Execute` runs a command, while `ReadFile`, `EditFile` and `WriteFile` work on its files. If you swap the environment underneath, the agent's work moves into a sandbox and the agent itself does not change. The page also says when to use `bash_tool` instead.
* [E2BEnvironment](integrations/e2b/e2b_environment/index.md) is a remote Linux sandbox where the agent can run commands, install packages and keep files. It needs an E2B account, and the sandbox has a time-to-live. If the sandbox reaches that limit, the data in it is lost, and nothing reports the loss.
* [DaytonaEnvironment](integrations/daytona/daytona_environment/index.md) is the second hosted sandbox, sitting behind the same interface as E2B. The page covers the three differences that change how you write your code, which is what you need to pick between them.

### Cloud and third-party toolsets

* [BigQueryToolset](integrations/bigquery/bigquery_toolset/index.md) gives an agent eleven tools for exploring and querying BigQuery. One setting, `write_mode`, decides whether the agent can change anything, and by default it refuses everything but `SELECT`.
* [GCSToolset and GCSAdminToolset](integrations/gcs/gcs_toolset/index.md) put Cloud Storage in front of an agent, split into the objects inside buckets and the buckets themselves. Both are read-only until you say otherwise, and getting that split right is the main decision.
* [Spanner, Bigtable, Pub/Sub and Data Agent toolsets](tools/cloud_data_toolsets/index.md) are four more Google Cloud data services as agent tools, shaped much like BigQuery. The page says which of them can write, and warns that `tool_filter` matches a name the model never sees.
* [APIHubToolset, ApplicationIntegrationToolset and ToolboxToolset](tools/enterprise_api_toolsets/index.md) are three ways to turn an API your organization already runs into agent tools. Whichever catalog your API is registered in decides the choice for you.
* [LangchainTool](integrations/langchain/langchain_tool/index.md) wraps an existing LangChain tool so an ADK agent can call it, and it lists which LangChain behaviors have no ADK equivalent.
* [CrewaiTool](integrations/crewai/crewai_tool/index.md) does the same for an existing CrewAI tool, including the `name` argument you have to supply and the way keyword arguments are passed through.
* [Model Armor](integrations/model_armor/index.md) screens what a user sends and what the model returns through Google Cloud Model Armor, which is what you reach for when prompt injection or unsafe output is a risk you have to answer for.

To use tools published by an MCP server, see
[McpToolset](tools/mcp_tool/mcp_toolset/index.md) under
[Remote agents, A2A and MCP](#remote-agents-a2a-and-mcp).

## Workflows

A workflow is a directed acyclic graph of nodes that runs in an order you
declare, rather than an order a model chooses turn by turn.

* [Workflow](workflow/workflow/index.md) is the orchestration node that executes the graph. Everything else in this area is a piece of a graph that a `Workflow` runs, so it is the one to read first. It covers parallel branches, dynamic scheduling, the workflow's output, and resuming from session events.
* [Workflow Graphs](workflow/graph/index.md) covers nodes, edges and the syntax that wires them together, along with the validation rules that reject a bad graph before it runs.
* [BaseNode](workflow/base_node/index.md) holds the options every node has whatever kind it is: its name, its input and output schemas, its timeout, its retries, and its resume behavior.
* [Function Nodes](workflow/function_node/index.md) let you use a plain function, coroutine or generator as a node. ADK wraps the callable for you, so most graphs need no node subclass at all.
* [ParallelWorker](workflow/parallel_worker/index.md) runs one node once per item of a list you give it, concurrently. The results come back in the order of the list, not the order the runs finished.
* [JoinNode](workflow/join_node/index.md) waits for every predecessor to finish before the graph continues. It is the fan-in half of a fan-out.
* [Dynamic Nodes](workflow/dynamic_nodes/index.md) choose the next node with `ctx.run_node()` in ordinary Python control flow, so you do not have to draw every edge in advance.
* [RetryConfig](workflow/retry_config/index.md) is the retry policy you attach to a node so that a transient failure does not take the whole graph down with it.

A node can pause the whole run to ask a person a question; see
[RequestInput](events/request_input/index.md). To let a model call a workflow,
see [A workflow node as a tool](tools/node_tool/index.md).

## Run an app

Running an agent means giving a `Runner` a user message and reading the events
it streams back. Serving over HTTP, live audio and telemetry all sit around
that one exchange rather than replacing it.

### The app and the runner

* [App](apps/app/index.md) is the top-level container. It binds a root agent to the application name, the plugins, and the configs for context caching, event compaction and resumability. Services attach to the runner instead, and the page explains why.
* [Runner and InMemoryRunner](runners/runner/index.md) is the object you call to execute an agent. It creates or loads the session, appends the user message, runs the agent tree, and streams `Event` objects back. `InMemoryRunner` is the version with nothing to configure.
* [Runner Rewind](runners/runner/rewind.md) undoes a turn with `rewind_async`, putting session state and artifacts back and hiding the invocation from the model. Read the list of what it does not undo before you rely on it.
* [Resumability](apps/resumability/index.md) lets an invocation stop on a long-running tool call and be picked up later under the same invocation id. ADK records where each agent stopped, and your application does the resuming.
* [Events Compaction](apps/events_compaction/index.md) replaces stretches of old conversation with a summary, so a long session stops outgrowing the context window. It covers the triggers and how to write your own summarizer.

### Read and steer the event stream

* [Event and NodeInfo](events/event/index.md) is the single record type ADK emits for everything that happens, from model replies and function calls to state changes and node output. Read it to know what to do with what `run_async` yields.
* [EventActions](events/event_actions/index.md) is the side channel for telling the framework something instead of telling the model: escalate out of a loop, skip summarization, transfer control. It rides on every event and is reachable as `ctx.actions`.
* [RequestInput](events/request_input/index.md) is the human-in-the-loop interrupt. It pauses a run to ask the person a structured question and then resumes with their answer, from a workflow node or from an `LlmAgent`.

### Live audio and streaming

* [Runner Live Streaming](runners/runner/live.md) covers `run_live`, which holds one open bidirectional session with a Gemini Multimodal Live API model so that audio and text flow in both directions while tools run in the background.
* [LiveRequestQueue](agents/live_request_queue/index.md) is the queue you push into during a live session, carrying text content, realtime audio blobs, and the signals that end a turn or close the stream.
* [Live model callbacks](flows/llm_flows/base_llm_flow/live_model_callbacks.md) lets you inspect or block content on a live bidirectional session, which is where you enforce a policy on audio that never passes through an ordinary turn.

### Serve over HTTP

* [get_fast_api_app](cli/fast_api/index.md) builds the same FastAPI app that `adk web` and `adk api_server` use and hands it back to you, so you can add your own routes, middleware and lifespan. It also covers the service URIs, the DNS-rebinding guard and custom agent loaders.
* [ServiceRegistry](cli/service_registry/index.md) registers a URI scheme such as `mystore://`, so `--session_service_uri` builds your session, artifact, memory or A2A task-store class instead of one of ADK's.

### When something goes wrong

* [ADK exceptions](errors/index.md) covers the six exceptions ADK raises on its own behalf: what raises each one, whether you should catch it, and why three of them subclass `ValueError`.
* [TelemetryConfig](telemetry/telemetry_config/index.md) describes what ADK puts on its OpenTelemetry spans, including the prompt and reply text that is included by default. Read it before pointing an exporter at anything shared.
* [Feature flags](features/feature_registry/index.md) turn unstable behavior on and off, either with the `ADK_ENABLE_<NAME>` and `ADK_DISABLE_<NAME>` environment variables or from Python.

## Sessions, state, memory and artifacts

A session is the record of one conversation, and state is the data carried
alongside it. Memory and artifacts reach past that: memory searches
conversations that have already ended, and artifacts hold files that are too
large or too binary to sit in an event history.

### Sessions and state

* [Session and BaseSessionService](sessions/session/index.md) covers what a conversation record holds, meaning its id, its user, its state and its ordered event history, and the interface that creates, reads, lists and deletes them. It also helps you choose a backend.
* [State](sessions/state/index.md) is the delta-aware view of session state that agents, tools and callbacks write through. A key's prefix, one of `app:`, `user:`, `temp:` or no prefix at all, decides how far the value travels and whether it is stored at all.

### Session backends

All five implement `BaseSessionService`, so switching from one to another does
not change your agent.

* [SqliteSessionService](sessions/sqlite_session_service/index.md) is a local SQLite file with no server to run and no extra dependency to install. The ADK CLI uses it by default. The page covers the `db_path` forms and the old-schema migration it refuses to skip.
* [DatabaseSessionService](sessions/database_session_service/index.md) works with any database SQLAlchemy can reach, and creates its own tables. If you point it at a database that already holds sessions, it detects which of the two schema versions that database is on, and it refuses a write that would overwrite a newer revision.
* [FirestoreSessionService](integrations/firestore/firestore_session_service/index.md) stores sessions as Firestore documents, so there is no database server for you to run. Writes are transactional and revision-checked, which stops a worker holding a stale session from clobbering a newer one.
* [RedisSessionService](integrations/redis/redis_session_service/index.md) keeps sessions in Redis, shared across processes without a relational database in the way. Unlike every other backend these expire, seven days after the last write by default, and concurrent writes are not checked.
* [VertexAiSessionService](sessions/vertex_ai_session_service/index.md) is the Vertex AI Agent Engine Sessions API. An agent deployed to Agent Engine uses this one, and it is the only backend where `app_name` has to be a reasoning engine id instead of a name you choose.

### Flows
* [Live model callbacks](flows/llm_flows/base_llm_flow/live_model_callbacks.md) - Inspecting or blocking content on a live bidirectional session.

### Integrations
* [Model Armor](integrations/model_armor/index.md) - Screening user input and model output with Google Cloud Model Armor.

### Memory

* [BaseMemoryService](memory/memory_service/index.md) stores finished conversations and searches them from a later one, so an agent recalls more than the session in front of it. The page also sets out where session state ends and memory begins.
* [Vertex AI memory services](memory/vertex_ai_memory/index.md) are the two managed backends. Memory Bank extracts durable facts, while the RAG corpus stores whole transcripts and retrieves passages from them. They share an interface but answer different questions.

### Artifacts

* [BaseArtifactService](artifacts/artifact_service/index.md) holds named binary blobs outside the conversation history, such as a generated report, a chart or an uploaded PDF. Every write makes a new numbered version, and if you prefix the filename with `user:`, the file is shared across every session that user has.

## Remote agents, A2A and MCP

Two protocols are involved. A2A, short for Agent2Agent, connects one agent to
another, and MCP, the Model Context Protocol, connects an agent to a tool
server.

### Serve your agent to others

* [to_a2a](a2a/utils/agent_to_a2a/index.md) turns an agent or a `Workflow` into a Starlette app that speaks A2A, so other agents can call it over HTTP. It puts you on the serving side of an A2A deployment, opposite [`RemoteA2aAgent`](agents/remote_a2a_agent/index.md).
* [AgentCardBuilder](a2a/utils/agent_card_builder/index.md) builds the card another agent reads before it decides whether to call yours. The card is where you control what the outside world sees.
* [A2aAgentExecutor](a2a/executor/a2a_agent_executor/index.md) is the server-side adapter between an incoming A2A request and an ADK `Runner`. It also gives you three interceptor hooks for traffic in both directions.
* [to_mcp_server](tools/mcp_tool/agent_to_mcp/index.md) exposes an agent as an MCP server, so any MCP host can drive it as a single tool. It is the MCP counterpart of `to_a2a`.

### Call agents and servers that run elsewhere

* [RemoteA2aAgent](agents/remote_a2a_agent/index.md) is a local stand-in for an agent running in another process. Put it in your agent tree like any other agent and ADK turns the conversation into A2A messages for you.
* [RemoteA2aAgent Task Mode](agents/remote_a2a_agent/task.md) covers `mode="task"`. If you set it, the remote agent becomes a bounded sub-task that reports back with `finish_task` rather than a peer the conversation moves to.
* [A2aRemoteAgentConfig](a2a/agent/config/index.md) is the `config=` argument of a `RemoteA2aAgent`. It holds the interceptors around every outgoing request, the headers on the agent-card fetch, and the converters that turn A2A responses back into ADK events.
* [McpToolset](tools/mcp_tool/mcp_toolset/index.md) consumes an MCP server's tools from an ADK agent, over stdio, SSE or streamable HTTP.

## Plugins and skills

A plugin changes how the whole application behaves. A skill changes what one
agent knows, and the agent loads it partway through a turn rather than carrying
it in its instruction the whole time.

### Plugins

A plugin's callbacks fire at fixed points of a run, for every agent in the
application, which is what separates a plugin from an agent callback.

* [Built-in plugins](plugins/builtin_plugins/index.md) are the seven that ship with ADK: console logging, YAML debug capture, automatic tracing, context trimming, an app-wide instruction, moving uploaded files into artifacts, and letting a tool return an image.
* [ReflectAndRetryModelPlugin](plugins/reflect_retry_model_plugin/index.md) retries a failed model turn by feeding the failure back to the model as guidance. It catches malformed function calls and similar errors, up to a limit you configure, and it holds up under concurrency.
* [ReflectAndRetryToolPlugin](plugins/reflect_retry_tool_plugin/index.md) does the same recovery for a tool that raised an exception or returned an error result, so the failure does not reach the user.

### Skills

* [Skill, Frontmatter, and Resources](skills/skill/index.md) covers the `SKILL.md` file format, the loader functions, and the progressive disclosure that keeps a skill's reference files out of the prompt until they are needed.
* [SkillRegistry](skills/skill_registry/index.md) is the interface for a searchable skill catalog that an agent discovers at run time, along with `GCPSkillRegistry`, the one implementation ADK ships.

To put skills in front of an agent, see
[SkillToolset](tools/skill_toolset/index.md).

## Evaluation and optimization

Evaluation replays recorded conversations and scores what the agent did, so the
effect of a change to an instruction or a tool is measured rather than guessed
at. Optimization then uses those same scores to rewrite the instruction.

* [AgentEvaluator](evaluation/agent_evaluator/index.md) is the supported way to check agent quality from a `pytest` suite, and the place to start. It replays recorded conversations, scores each answer and tool call, and fails the test when a score drops below its threshold.
* [EvalConfig and the eval config file](evaluation/eval_config/index.md) is the reference for the JSON config that says which metrics run and how strict each one is. It covers where the file is found, all thirteen metrics, and which criterion keys are legal under each of them.
* [BaseEvalService and LocalEvalService](evaluation/eval_service/index.md) split evaluation into two phases you call separately, so a CI job can run the agent once and then score the results as often as it likes. `AgentEvaluator` and `adk eval` both sit on top of this.
* [Evaluator](evaluation/evaluator/index.md) is how you write a metric the built-in thirteen do not cover, either as a plain function or as a class.
* [AgentOptimizer and Sampler](optimization/agent_optimizer/index.md) rewrite an agent's instruction automatically by scoring candidate prompts against an eval set. You supply the `Sampler` that evaluates your agent, and ADK drives the search.
