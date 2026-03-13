import type { ReactNode } from 'react';
import { BookText, BrainCircuit, FileSearch, LibraryBig, Quote, ShieldCheck, Sparkles } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { GraphRAGResponse } from '../../types';
import type {
  GraphRAGMetadata,
  ResearchGraphClaim,
  ResearchGraphDecision,
  ResearchGraphFacet,
  ResearchGraphPayload,
  ResearchGraphStage,
  ResearchGraphToolCall,
  ResearchGraphWork,
  ResearchStageStatus,
} from '../../types/graphrag';

interface ResearchGraphPanelProps {
  response: GraphRAGResponse | null;
  className?: string;
}

function getMetadata(response: GraphRAGResponse | null): GraphRAGMetadata | undefined {
  return response?.metadata;
}

function buildFallbackResearchGraph(response: GraphRAGResponse): ResearchGraphPayload {
  const quality = response.quality_metrics;
  const reasoning = response.reasoning_path;
  const startingNodes = reasoning?.starting_nodes ?? [];
  const expandedNodes = reasoning?.expanded_nodes ?? [];
  const traversedEdges = reasoning?.traversed_edges ?? [];
  const sources = response.sources ?? [];

  return {
    overview: {
      query_type: getMetadata(response)?.query_type ?? 'legacy',
      complexity: getMetadata(response)?.complexity ?? 'unknown',
      grounding_policy: getMetadata(response)?.grounding_policy ?? 'mixed',
      quality_badge: quality?.quality_badge ?? 'unknown',
      pipeline_degraded: Boolean(getMetadata(response)?.pipeline_degraded),
      claim_ledger_mode: getMetadata(response)?.claim_ledger_mode ?? 'legacy',
      render_answer_mode: getMetadata(response)?.render_answer_mode ?? 'legacy',
      scholarly_polish_mode: getMetadata(response)?.scholarly_polish_mode ?? 'legacy',
      seed_node_count: startingNodes.length || response.nodes_used,
      context_node_count: expandedNodes.length || response.nodes_used,
      bundle_count: 0,
      work_count: 0,
      claim_count: 0,
      citation_count: response.citations?.ancient_sources?.length ?? 0,
      tool_call_count: 0,
      decision_count: 0,
    },
    stages: [
      {
        id: 'legacy_search',
        title: 'Retrieve source nodes',
        status: 'complete',
        summary: `${startingNodes.length || response.nodes_used || 0} seed nodes retrieved from the legacy GraphRAG pipeline.`,
        metrics: [
          { label: 'Seeds', value: startingNodes.length || response.nodes_used || 0 },
          { label: 'Sources', value: sources.length },
        ],
        details: {
          starting_nodes: startingNodes.slice(0, 12),
          sources: sources.slice(0, 12),
        },
      },
      {
        id: 'legacy_traversal',
        title: 'Traverse reasoning graph',
        status: 'complete',
        summary: `${expandedNodes.length || response.nodes_used || 0} expanded nodes and ${traversedEdges.length || response.edges_traversed || 0} edges traversed.`,
        metrics: [
          { label: 'Expanded', value: expandedNodes.length || response.nodes_used || 0 },
          { label: 'Edges', value: traversedEdges.length || response.edges_traversed || 0 },
        ],
        details: {
          expanded_nodes: expandedNodes.slice(0, 12),
          traversed_edges: traversedEdges.slice(0, 12),
        },
      },
      {
        id: 'legacy_synthesis',
        title: 'Synthesize answer',
        status: 'complete',
        summary: `${response.answer.length} characters generated with ${response.citations?.ancient_sources?.length ?? 0} visible ancient citations.`,
        metrics: [
          { label: 'Chars', value: response.answer.length },
          { label: 'Confidence', value: quality?.confidence_score },
          { label: 'Badge', value: quality?.quality_badge ?? 'unknown' },
        ],
        details: {
          answer_excerpt: response.answer.slice(0, 800),
          llm_provider: response.llm_provider,
          llm_model: response.llm_model,
        },
      },
    ],
    facets: [],
    works: [],
    claims: [],
    hypotheses: [],
    open_questions: [],
    counter_evidence: [],
    uncertainties: [],
    tool_calls: [],
    reading_decisions: [],
  };
}

function getResearchGraph(response: GraphRAGResponse | null): ResearchGraphPayload | undefined {
  if (!response) {
    return undefined;
  }

  return getMetadata(response)?.research_graph ?? buildFallbackResearchGraph(response);
}

function statusTheme(status: ResearchStageStatus) {
  if (status === 'degraded') {
    return 'border-rose-200/80 bg-rose-50/90 text-rose-700';
  }
  if (status === 'skipped') {
    return 'border-stone-200/80 bg-stone-100/70 text-stone-500';
  }
  return 'border-emerald-200/80 bg-emerald-50/90 text-emerald-700';
}

function formatPercent(value: unknown) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '--';
  }
  return `${Math.round(value * 100)}%`;
}

function formatEvidenceClass(value: string) {
  return value.replace(/_/g, ' ');
}

function MetricPill({ label, value }: { label: string; value: string | number | boolean | null | undefined }) {
  if (value === undefined || value === null || value === '') {
    return null;
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-stone-200/80 bg-white/85 px-2 py-1 text-[10px] font-medium text-stone-600">
      <span className="font-semibold text-stone-800">{String(value)}</span>
      {label}
    </span>
  );
}

function Section({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: typeof BrainCircuit;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[24px] border border-stone-200/80 bg-white/78 p-4 shadow-[0_18px_36px_-30px_rgba(120,53,15,0.28)]">
      <div className="flex items-center gap-2 text-sm font-semibold text-stone-900">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-2xl bg-parchment-100 text-amber-700">
          <Icon className="h-4 w-4" />
        </span>
        {title}
      </div>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function OverviewSection({ graph }: { graph: ResearchGraphPayload }) {
  const overview = graph.overview;

  return (
    <Section title="Research Overview" icon={BrainCircuit}>
      <div className="grid gap-2 md:grid-cols-2">
        {[
          { label: 'Type', value: overview.query_type },
          { label: 'Complexity', value: overview.complexity },
          { label: 'Grounding', value: overview.grounding_policy },
          { label: 'Quality', value: overview.quality_badge },
          { label: 'Seeds', value: overview.seed_node_count },
          { label: 'Context', value: overview.context_node_count },
          { label: 'Bundles', value: overview.bundle_count },
          { label: 'Claims', value: overview.claim_count },
          { label: 'Citations', value: overview.citation_count },
          { label: 'Tools', value: overview.tool_call_count },
          { label: 'Decisions', value: overview.decision_count },
          { label: 'Ledger', value: overview.claim_ledger_mode },
          { label: 'Render', value: overview.render_answer_mode },
          { label: 'Polish', value: overview.scholarly_polish_mode },
        ].map((item) => (
          <div
            key={item.label}
            className="rounded-2xl border border-stone-200/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(252,249,244,0.95))] px-3 py-2"
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-400">{item.label}</p>
            <p className="mt-1 text-sm font-semibold text-stone-900">{item.value ?? '--'}</p>
          </div>
        ))}
      </div>
      {overview.pipeline_degraded && (
        <p className="mt-3 rounded-2xl border border-rose-200/80 bg-rose-50/85 px-3 py-2 text-xs leading-5 text-rose-700">
          The pipeline degraded during this run. The right panel is showing the exact modes used so you can inspect where fallback happened.
        </p>
      )}
    </Section>
  );
}

function StageCard({ stage }: { stage: ResearchGraphStage }) {
  return (
    <article className="rounded-[22px] border border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(251,248,242,0.96))] p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-stone-900">{stage.title}</p>
          <p className="mt-1 text-xs leading-5 text-stone-500">{stage.summary}</p>
        </div>
        <span className={cn('inline-flex rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]', statusTheme(stage.status))}>
          {stage.status}
        </span>
      </div>
      {stage.metrics && stage.metrics.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {stage.metrics.map((metric) => (
            <MetricPill key={`${stage.id}-${metric.label}`} label={metric.label} value={metric.value} />
          ))}
        </div>
      )}
      {stage.details && (
        <details className="mt-3 rounded-2xl border border-stone-200/70 bg-stone-50/70 p-2" open={stage.status !== 'complete'}>
          <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-500">
            Trace details
          </summary>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-stone-600">
            {JSON.stringify(stage.details, null, 2)}
          </pre>
        </details>
      )}
    </article>
  );
}

function FacetCard({ facet }: { facet: ResearchGraphFacet }) {
  return (
    <article className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-stone-900">{facet.title}</p>
          <p className="mt-1 text-xs leading-5 text-stone-500">{facet.question}</p>
        </div>
        <span className="inline-flex rounded-full border border-amber-200/80 bg-amber-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-700">
          P{facet.priority ?? 1}
        </span>
      </div>
      {facet.summary && <p className="mt-3 text-xs leading-5 text-stone-600">{facet.summary}</p>}
      <div className="mt-3 flex flex-wrap gap-1.5">
        <MetricPill label="direct" value={facet.primary_count} />
        <MetricPill label="testimony" value={facet.testimony_count} />
        <MetricPill label="counter" value={facet.counter_count} />
        <MetricPill label="metadata" value={facet.metadata_count} />
        <MetricPill label="notes" value={facet.note_count} />
      </div>
    </article>
  );
}

function WorkCard({ work }: { work: ResearchGraphWork }) {
  return (
    <article className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-stone-900">{work.title}</p>
          {work.author && <p className="mt-1 text-xs italic leading-5 text-stone-500">{work.author}</p>}
        </div>
        {work.has_translation && (
          <span className="inline-flex rounded-full border border-blue-200/80 bg-blue-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-blue-700">
            translation
          </span>
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        <MetricPill label="bundles" value={work.bundle_count} />
        <MetricPill label="sections" value={work.section_count} />
        <MetricPill label="direct" value={work.primary_count} />
        <MetricPill label="testimony" value={work.testimony_count} />
        <MetricPill label="counter" value={work.counter_count} />
      </div>
      {work.canonical_refs.length > 0 && (
        <p className="mt-3 text-xs leading-5 text-stone-600">
          Refs: {work.canonical_refs.join(', ')}
        </p>
      )}
      {work.sections.length > 0 && (
        <div className="mt-3 flex flex-col gap-2">
          {work.sections.map((section) => (
            <div
              key={`${work.work_id}-${section.node_id ?? section.path ?? section.title}`}
              className="rounded-2xl border border-stone-200/70 bg-stone-50/70 px-3 py-2 text-xs leading-5 text-stone-600"
            >
              <p className="font-medium text-stone-800">{section.title || section.path || 'Selected section'}</p>
              {section.path && <p className="mt-1 text-stone-500">{section.path}</p>}
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

function ClaimCard({ claim }: { claim: ResearchGraphClaim }) {
  return (
    <article className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="inline-flex rounded-full border border-amber-200/80 bg-amber-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-700">
          {formatEvidenceClass(claim.evidence_class)}
        </span>
        <span className="inline-flex rounded-full border border-stone-200/80 bg-stone-100/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-600">
          {claim.support_type}
        </span>
        <span className="inline-flex rounded-full border border-stone-200/80 bg-stone-100/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-600">
          {claim.status}
        </span>
        <span className="inline-flex rounded-full border border-emerald-200/80 bg-emerald-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
          {formatPercent(claim.confidence)}
        </span>
      </div>
      <p className="mt-3 text-sm leading-6 text-stone-900">{claim.claim}</p>
      {claim.refs.length > 0 && (
        <p className="mt-2 text-xs font-medium leading-5 text-stone-500">
          Refs: {claim.refs.join(', ')}
        </p>
      )}
      {claim.quote_original && (
        <blockquote className="mt-3 rounded-2xl border border-stone-200/70 bg-stone-50/70 px-3 py-2 text-xs leading-5 text-stone-700">
          {claim.quote_original}
        </blockquote>
      )}
      {claim.quote_translation && (
        <blockquote className="mt-2 rounded-2xl border border-blue-200/70 bg-blue-50/70 px-3 py-2 text-xs leading-5 text-blue-900">
          {claim.quote_translation}
        </blockquote>
      )}
    </article>
  );
}

function formatToolName(value: string) {
  return value.replace(/_/g, ' ');
}

function ToolCallCard({ toolCall }: { toolCall: ResearchGraphToolCall }) {
  return (
    <article className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="inline-flex rounded-full border border-sky-200/80 bg-sky-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-sky-700">
          {formatToolName(toolCall.tool_name)}
        </span>
        <span className="inline-flex rounded-full border border-stone-200/80 bg-stone-100/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-600">
          {toolCall.stage_id}
        </span>
        <span className="inline-flex rounded-full border border-stone-200/80 bg-stone-100/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-600">
          {toolCall.status}
        </span>
      </div>
      {toolCall.query && <p className="mt-3 text-xs leading-5 text-stone-600">Query: {toolCall.query}</p>}
      {toolCall.rationale && <p className="mt-2 text-xs leading-5 text-stone-600">{toolCall.rationale}</p>}
      <div className="mt-3 flex flex-wrap gap-1.5">
        <MetricPill label="selected" value={toolCall.detail_count} />
        <MetricPill label="work" value={toolCall.work_title} />
      </div>
      {toolCall.section_path && (
        <p className="mt-2 text-xs leading-5 text-stone-500">{toolCall.section_path}</p>
      )}
      {toolCall.selected_ids.length > 0 && (
        <p className="mt-2 text-xs leading-5 text-stone-500">IDs: {toolCall.selected_ids.join(', ')}</p>
      )}
      {toolCall.details && (
        <details className="mt-3 rounded-2xl border border-stone-200/70 bg-stone-50/70 p-2">
          <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-500">
            Tool details
          </summary>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-stone-600">
            {JSON.stringify(toolCall.details, null, 2)}
          </pre>
        </details>
      )}
    </article>
  );
}

function DecisionCard({ decision }: { decision: ResearchGraphDecision }) {
  return (
    <article className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="inline-flex rounded-full border border-emerald-200/80 bg-emerald-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
          {formatToolName(decision.decision_type)}
        </span>
        <span className="inline-flex rounded-full border border-stone-200/80 bg-stone-100/80 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-stone-600">
          {decision.stage_id}
        </span>
        {decision.facet_id && (
          <span className="inline-flex rounded-full border border-amber-200/80 bg-amber-50/90 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-700">
            {decision.facet_id}
          </span>
        )}
      </div>
      <p className="mt-3 text-sm font-semibold text-stone-900">{decision.title}</p>
      {decision.rationale && <p className="mt-2 text-xs leading-5 text-stone-600">{decision.rationale}</p>}
      <div className="mt-3 flex flex-wrap gap-1.5">
        <MetricPill label="selected" value={decision.selected_ids.length} />
        <MetricPill label="rejected" value={decision.rejected_ids.length} />
        <MetricPill label="refs" value={decision.supporting_refs.length} />
      </div>
      {decision.supporting_refs.length > 0 && (
        <p className="mt-2 text-xs font-medium leading-5 text-stone-500">
          Refs: {decision.supporting_refs.join(', ')}
        </p>
      )}
      {decision.selected_ids.length > 0 && (
        <p className="mt-2 text-xs leading-5 text-stone-500">
          Selected: {decision.selected_ids.join(', ')}
        </p>
      )}
      {decision.rejected_ids.length > 0 && (
        <p className="mt-1 text-xs leading-5 text-stone-500">
          Rejected: {decision.rejected_ids.join(', ')}
        </p>
      )}
      {decision.metadata && (
        <details className="mt-3 rounded-2xl border border-stone-200/70 bg-stone-50/70 p-2">
          <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-500">
            Decision details
          </summary>
          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-stone-600">
            {JSON.stringify(decision.metadata, null, 2)}
          </pre>
        </details>
      )}
    </article>
  );
}

function ListBlock({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">{title}</p>
      <ul className="mt-2 space-y-2">
        {items.map((item, index) => (
          <li key={`${title}-${index}`} className="rounded-2xl border border-stone-200/70 bg-stone-50/70 px-3 py-2 text-xs leading-5 text-stone-700">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ResearchGraphPanel({
  response,
  className,
}: ResearchGraphPanelProps) {
  const graph = getResearchGraph(response);

  if (!response) {
    return null;
  }

  if (!graph) {
    return (
      <div className={cn('h-full overflow-y-auto rounded-[24px] border border-dashed border-stone-300 bg-white/70 px-4 py-5 text-sm text-stone-500', className)}>
        Structured reasoning metadata is not available for this response yet. Once the backend emits a `research_graph`, every stage of retrieval, dossier-building, and verification will appear here.
      </div>
    );
  }

  return (
    <div className={cn('h-full overflow-y-auto pr-1', className)}>
      <div className="flex flex-col gap-3">
        <OverviewSection graph={graph} />

        <Section title="Reasoning Stages" icon={Sparkles}>
          <div className="space-y-3">
            {graph.stages.map((stage) => (
              <StageCard key={stage.id} stage={stage} />
            ))}
          </div>
        </Section>

        {graph.facets.length > 0 && (
          <Section title="Research Facets" icon={FileSearch}>
            <div className="grid gap-3">
              {graph.facets.map((facet) => (
                <FacetCard key={facet.facet_id} facet={facet} />
              ))}
            </div>
          </Section>
        )}

        {graph.works.length > 0 && (
          <Section title="Selected Works" icon={LibraryBig}>
            <div className="grid gap-3">
              {graph.works.map((work) => (
                <WorkCard key={work.work_id} work={work} />
              ))}
            </div>
          </Section>
        )}

        {graph.claims.length > 0 && (
          <Section title="Grounded Claims" icon={Quote}>
            <div className="grid gap-3">
              {graph.claims.map((claim, index) => (
                <ClaimCard key={`${claim.claim}-${index}`} claim={claim} />
              ))}
            </div>
          </Section>
        )}

        {graph.tool_calls.length > 0 && (
          <Section title="Reading Tools" icon={Sparkles}>
            <div className="grid gap-3">
              {graph.tool_calls.map((toolCall) => (
                <ToolCallCard key={toolCall.tool_call_id} toolCall={toolCall} />
              ))}
            </div>
          </Section>
        )}

        {graph.reading_decisions.length > 0 && (
          <Section title="Reading Decisions" icon={ShieldCheck}>
            <div className="grid gap-3">
              {graph.reading_decisions.map((decision) => (
                <DecisionCard key={decision.decision_id} decision={decision} />
              ))}
            </div>
          </Section>
        )}

        <Section title="Research Notebook" icon={BookText}>
          <div className="grid gap-3">
            <ListBlock title="Hypotheses" items={graph.hypotheses} />
            <ListBlock title="Open questions" items={graph.open_questions} />
            <ListBlock title="Counter-evidence" items={graph.counter_evidence} />
            <ListBlock title="Uncertainties" items={graph.uncertainties} />
          </div>
        </Section>

        <Section title="Grounding Discipline" icon={ShieldCheck}>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">Rendering modes</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <MetricPill label="ledger" value={graph.overview.claim_ledger_mode} />
                <MetricPill label="render" value={graph.overview.render_answer_mode} />
                <MetricPill label="polish" value={graph.overview.scholarly_polish_mode} />
              </div>
            </div>
            <div className="rounded-[22px] border border-stone-200/80 bg-white/88 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-stone-500">Final grounding</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                <MetricPill label="quality" value={graph.overview.quality_badge} />
                <MetricPill label="citations" value={graph.overview.citation_count} />
                <MetricPill label="policy" value={graph.overview.grounding_policy} />
              </div>
            </div>
          </div>
        </Section>
      </div>
    </div>
  );
}
