import Lake
open Lake DSL

package «pq-aggregation» where
  leanOptions := #[⟨`autoImplicit, false⟩]

require "leanprover-community" / "mathlib" @ git "v4.36.0"

@[default_target]
lean_lib PQAggregation where
