import { motion } from "framer-motion";

// Renders the citation as distinct cyan chips. Each field is optional; only
// non-null fields produce a chip. Returns nothing if there's no citation at all.
//
// citation shape: { document, section, clause, page } | null
export default function CitationBlock({ citation }) {
  if (!citation) return null;

  const { document, section, clause, page } = citation;

  const chips = [];
  if (document) chips.push({ label: "Document", value: document });
  if (section) chips.push({ label: "Section", value: section });
  if (clause) chips.push({ label: "Clause", value: clause });
  if (page !== null && page !== undefined) chips.push({ label: "Page", value: page });

  if (chips.length === 0) return null;

  const container = {
    hidden: {},
    show: { transition: { staggerChildren: 0.05 } },
  };
  const chip = {
    hidden: { opacity: 0, scale: 0.9 },
    show: { opacity: 1, scale: 1, transition: { duration: 0.25 } },
  };

  return (
    <div className="mt-5">
      <p className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">
        Citation
      </p>
      <motion.div
        className="flex flex-wrap gap-2"
        variants={container}
        initial="hidden"
        animate="show"
      >
        {chips.map((c) => (
          <motion.span
            key={c.label}
            variants={chip}
            className="inline-flex items-center gap-1.5 rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1 text-sm text-accent"
          >
            <span className="text-[11px] font-medium uppercase tracking-wide text-cyan-300/70">
              {c.label}
            </span>
            <span className="font-medium text-cyan-100">{c.value}</span>
          </motion.span>
        ))}
      </motion.div>
    </div>
  );
}
