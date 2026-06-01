#!/usr/bin/env Rscript
# Regenerate JSON fixtures from R FactoMineR for the parity tests.
#
# Usage: Rscript tools/refresh_r_fixtures.R
#
# Output: tests/fixtures/r_outputs/<method>/<dataset>.json

suppressPackageStartupMessages({
  library(FactoMineR)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = FALSE)
script_arg <- args[grep("^--file=", args)]
if (length(script_arg) == 1) {
  script_path <- normalizePath(sub("^--file=", "", script_arg))
  root <- normalizePath(file.path(dirname(script_path), ".."))
} else if (!is.null(sys.frame(1)$ofile)) {
  root <- normalizePath(file.path(dirname(sys.frame(1)$ofile), ".."))
} else {
  root <- normalizePath(getwd())
}
out_dir <- function(method) {
  d <- file.path(root, "tests", "fixtures", "r_outputs", method)
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
  d
}

write_json <- function(obj, path) {
  writeLines(toJSON(obj, digits = 10, auto_unbox = TRUE, pretty = FALSE, na = "string"), path)
}

dump_block <- function(block) {
  if (is.null(block)) return(NULL)
  cap <- function(name) if (!is.null(block[[name]])) as.data.frame(block[[name]]) else NULL
  list(
    coord   = cap("coord"),
    cos2    = cap("cos2"),
    contrib = cap("contrib"),
    cor     = cap("cor"),
    dist    = if (!is.null(block$dist)) as.numeric(block$dist) else NULL,
    inertia = if (!is.null(block$inertia)) as.numeric(block$inertia) else NULL,
    v.test  = cap("v.test"),
    eta2    = cap("eta2")
  )
}

dump_pca <- function(res) {
  list(
    eig     = as.data.frame(res$eig),
    var     = dump_block(res$var),
    ind     = dump_block(res$ind),
    ind.sup = dump_block(res$ind.sup),
    quanti.sup = dump_block(res$quanti.sup),
    quali.sup  = dump_block(res$quali.sup),
    svd     = list(vs = as.numeric(res$svd$vs))
  )
}

dump_ca <- function(res) {
  list(
    eig     = as.data.frame(res$eig),
    row     = dump_block(res$row),
    col     = dump_block(res$col),
    row.sup = dump_block(res$row.sup),
    col.sup = dump_block(res$col.sup),
    svd     = list(vs = as.numeric(res$svd$vs))
  )
}

dump_mca <- function(res) {
  list(
    eig = as.data.frame(res$eig),
    var = dump_block(res$var),
    ind = dump_block(res$ind),
    svd = list(vs = as.numeric(res$svd$vs))
  )
}

dump_famd <- function(res) {
  list(
    eig        = as.data.frame(res$eig),
    ind        = dump_block(res$ind),
    var        = dump_block(res$var),
    quanti.var = dump_block(res$quanti.var),
    quali.var  = dump_block(res$quali.var),
    quanti.sup = dump_block(res$quanti.sup),   # NULL (dropped) for the active-only fixture
    quali.sup  = dump_block(res$quali.sup),
    var.coord.sup = if (!is.null(res$var$coord.sup)) as.data.frame(res$var$coord.sup) else NULL,
    var.cos2.sup  = if (!is.null(res$var$cos2.sup))  as.data.frame(res$var$cos2.sup)  else NULL,
    svd        = list(vs = as.numeric(res$svd$vs))
  )
}

dump_mfa <- function(res) {
  grp <- res$group
  pax <- res$partial.axes
  list(
    eig        = as.data.frame(res$eig),
    ind        = dump_block(res$ind),
    ind.coord.partiel = if (!is.null(res$ind$coord.partiel)) as.data.frame(res$ind$coord.partiel) else NULL,
    quanti.var = dump_block(res$quanti.var),
    quali.var  = dump_block(res$quali.var),
    group = list(
      coord       = if (!is.null(grp$coord))       as.data.frame(grp$coord)       else NULL,
      contrib     = if (!is.null(grp$contrib))     as.data.frame(grp$contrib)     else NULL,
      cos2        = if (!is.null(grp$cos2))        as.data.frame(grp$cos2)        else NULL,
      dist2       = if (!is.null(grp$dist2))       as.numeric(grp$dist2)          else NULL,
      correlation = if (!is.null(grp$correlation)) as.data.frame(grp$correlation) else NULL,
      Lg          = if (!is.null(grp$Lg))          as.data.frame(grp$Lg)          else NULL,
      RV          = if (!is.null(grp$RV))          as.data.frame(grp$RV)          else NULL
    ),
    partial.axes = list(
      coord   = if (!is.null(pax$coord))   as.data.frame(pax$coord)   else NULL,
      cor     = if (!is.null(pax$cor))     as.data.frame(pax$cor)     else NULL,
      contrib = if (!is.null(pax$contrib)) as.data.frame(pax$contrib) else NULL
    ),
    inertia.ratio = if (!is.null(res$inertia.ratio)) as.numeric(res$inertia.ratio) else NULL,
    svd        = list(vs = as.numeric(res$svd$vs))
  )
}

dump_hmfa <- function(res) {
  grp <- res$group
  list(
    eig        = as.data.frame(res$eig),
    ind        = dump_block(res$ind),
    quanti.var = dump_block(res$quanti.var),
    quali.var  = dump_block(res$quali.var),
    group = list(
      coord     = lapply(grp$coord, as.data.frame),  # one data.frame per hierarchy level
      canonical = as.data.frame(grp$canonical)
    )
  )
}

dump_dmfa <- function(res) {
  list(
    eig         = as.data.frame(res$eig),
    ind         = dump_block(res$ind),       # already reordered to input row order
    var         = dump_block(res$var),
    quanti.sup  = dump_block(res$quanti.sup),
    group = list(
      coord   = as.data.frame(res$group$coord),
      coord.n = as.data.frame(res$group$coord.n),
      cos2    = as.data.frame(res$group$cos2)
    ),
    cor.dim.gr  = lapply(res$cor.dim.gr,  as.data.frame),  # one frame per group level
    var.partiel = lapply(res$var.partiel, as.data.frame),
    svd         = list(vs = as.numeric(res$svd$vs))
  )
}

# ---- PCA on decathlon ------------------------------------------------------
data(decathlon)
res_pca <- PCA(decathlon, scale.unit = TRUE, ncp = 5,
               quanti.sup = 11:12, quali.sup = 13, graph = FALSE)
write_json(dump_pca(res_pca), file.path(out_dir("pca"), "decathlon.json"))
cat("[fixtures] pca/decathlon.json\n")

# Also dump active-only (no sup) variant for cleaner structural checks
res_pca_plain <- PCA(decathlon[, 1:10], scale.unit = TRUE, ncp = 5, graph = FALSE)
write_json(dump_pca(res_pca_plain), file.path(out_dir("pca"), "decathlon_plain.json"))
cat("[fixtures] pca/decathlon_plain.json\n")

# ---- CA on children --------------------------------------------------------
data(children)
res_ca <- CA(children, row.sup = 15:18, col.sup = 6:8, graph = FALSE)
write_json(dump_ca(res_ca), file.path(out_dir("ca"), "children.json"))
cat("[fixtures] ca/children.json\n")

res_ca_plain <- CA(children[1:14, 1:5], graph = FALSE)
write_json(dump_ca(res_ca_plain), file.path(out_dir("ca"), "children_plain.json"))
cat("[fixtures] ca/children_plain.json\n")

# ---- MCA on tea ------------------------------------------------------------
data(tea)
# Use a small slice of tea: 18 active categorical vars, with a few sup numeric/quali
res_mca <- MCA(tea, quanti.sup = 19, quali.sup = c(20:36), ncp = 5, graph = FALSE)
write_json(dump_mca(res_mca), file.path(out_dir("mca"), "tea.json"))
cat("[fixtures] mca/tea.json\n")

# ---- FAMD on poison --------------------------------------------------------
# Read the committed CSV directly (instead of data(poison)) so the R input is
# byte-identical to what factominer.datasets.load_poison() reads on the Python
# side: index in column 1, strings -> factors with alphabetically-sorted levels
# (which matches pandas' .astype("category")), Age/Time stay integer.
poison_csv <- file.path(root, "factominer", "datasets", "data", "poison.csv")
poison <- read.csv(poison_csv, row.names = 1, check.names = FALSE, stringsAsFactors = TRUE)
res_famd <- FAMD(poison, ncp = 5, graph = FALSE)
write_json(dump_famd(res_famd), file.path(out_dir("famd"), "poison.json"))
cat("[fixtures] famd/poison.json\n")

# ---- FAMD on poison with supplementary variables ---------------------------
# Time (quanti) and Sex (quali) are supplementary; reuses the byte-identical
# poison read above. Exercises FAMD's sup-quanti + sup-quali machinery.
res_famd_sup <- FAMD(poison, ncp = 5, sup.var = c("Time", "Sex"), graph = FALSE)
write_json(dump_famd(res_famd_sup), file.path(out_dir("famd"), "poison_sup.json"))
cat("[fixtures] famd/poison_sup.json\n")

# ---- MFA on poison ---------------------------------------------------------
# Canonical FactoMineR poison MFA example, all groups active (no num.group.sup),
# reusing the byte-identical `poison` read above. group=c(2,2,5,6):
#   desc    = Age, Time                            (type "s", standardized quanti)
#   desc2   = Sick, Sex                            (type "n", categorical)
#   symptom = Nausea, Vomiting, Abdominals, Fever, Diarrhae   (type "n")
#   eat     = Potato, Fish, Mayo, Courgette, Cheese, Icecream (type "n")
res_mfa <- MFA(poison,
               group      = c(2L, 2L, 5L, 6L),
               type       = c("s", "n", "n", "n"),
               name.group = c("desc", "desc2", "symptom", "eat"),
               graph      = FALSE)
write_json(dump_mfa(res_mfa), file.path(out_dir("mfa"), "poison.json"))
cat("[fixtures] mfa/poison.json\n")

# ---- HMFA on poison (2-level hierarchy) ------------------------------------
# Reuses the byte-identical poison read. Level 1 = the canonical MFA grouping
# (desc/desc2/symptom/eat); level 2 = description={desc,desc2}, signs={symptom,eat}.
res_hmfa <- HMFA(poison,
                 H    = list(c(2L, 2L, 5L, 6L), c(2L, 2L)),
                 type = c("s", "n", "n", "n"),
                 graph = FALSE)
write_json(dump_hmfa(res_hmfa), file.path(out_dir("hmfa"), "poison.json"))
cat("[fixtures] hmfa/poison.json\n")

# ---- HMFA on decathlon events (pure-quanti sanity) -------------------------
# 10 numeric event columns, 3 elementary groups of sizes 4/3/3, 2 super-groups
# {group1} and {group2, group3}. All type "s"; no categorical path.
deca10 <- decathlon[, 1:10]
res_hmfa_d <- HMFA(deca10,
                   H    = list(c(4L, 3L, 3L), c(1L, 2L)),
                   type = rep("s", 3),
                   graph = FALSE)
write_json(dump_hmfa(res_hmfa_d), file.path(out_dir("hmfa"), "decathlon.json"))
cat("[fixtures] hmfa/decathlon.json\n")

# ---- DMFA on decathlon (Competition as grouping factor) --------------------
# After read.csv(row.names=1): cols 1-10 = events, 11 = Rank, 12 = Points,
# 13 = Competition (Decastar n=13 / OlympicG n=28). num.fact=13 -> Competition;
# Rank/Points are supplementary quanti. data(decathlon) == the bundled CSV.
res_dmfa <- DMFA(decathlon, num.fact = 13, scale.unit = TRUE, ncp = 5,
                 quanti.sup = c(11, 12), graph = FALSE)
write_json(dump_dmfa(res_dmfa), file.path(out_dir("dmfa"), "decathlon.json"))
cat("[fixtures] dmfa/decathlon.json\n")

# ---- GPA on the synthetic K=3 configuration dataset ------------------------
# R's GPA is stochastic (random multi-start + rnorm basis completion), so we
# set.seed for reproducibility of R's side. RV / RVs / simi are computed from
# the raw configs and are deterministic regardless. Reads the committed CSV for
# byte-identical input.
gpa_csv <- file.path(root, "factominer", "datasets", "data", "gpa_synth.csv")
gpa_df <- read.csv(gpa_csv, row.names = 1, check.names = FALSE)
set.seed(42)
res_gpa <- GPA(gpa_df, group = c(2, 2, 2), scale = TRUE, graph = FALSE)
xfin_list <- lapply(seq_len(dim(res_gpa$Xfin)[3]),
                    function(k) as.data.frame(res_gpa$Xfin[, , k]))
write_json(
  list(
    RV        = as.data.frame(res_gpa$RV),
    RVs       = as.data.frame(res_gpa$RVs),
    simi      = as.data.frame(res_gpa$simi),
    scaling   = as.numeric(res_gpa$scaling),
    consensus = as.data.frame(res_gpa$consensus),
    Xfin      = xfin_list,
    group     = c(2L, 2L, 2L)
  ),
  file.path(out_dir("gpa"), "synth.json")
)
cat("[fixtures] gpa/synth.json\n")

# ---- plot data: coord.ellipse on PCA(decathlon) individuals ----------------
# The only genuinely-derived plot quantity not already covered by the analysis
# fixtures is the confidence/concentration ellipse. Dump the EXACT input coords
# (factor + Dim.1/Dim.2) alongside coord.ellipse's output for both bary modes,
# so the Python test is a pure formula check (same coords in -> same ellipse).
coord_simul <- cbind.data.frame(
  Competition = decathlon[, "Competition"],
  res_pca$ind$coord[, 1:2]
)
ell_indiv <- coord.ellipse(coord_simul, axes = c(1, 2), level.conf = 0.95, npoint = 100, bary = FALSE)
ell_bary  <- coord.ellipse(coord_simul, axes = c(1, 2), level.conf = 0.95, npoint = 100, bary = TRUE)
write_json(
  list(
    coord_simul   = as.data.frame(coord_simul),
    ellipse_indiv = as.data.frame(ell_indiv$res),
    ellipse_bary  = as.data.frame(ell_bary$res),
    npoint = 100L,
    level = 0.95
  ),
  file.path(out_dir("plot"), "ellipse_decathlon.json")
)
cat("[fixtures] plot/ellipse_decathlon.json\n")

# ---- HCPC on PCA(decathlon) -----------------------------------------------
res_hcpc <- HCPC(res_pca_plain, nb.clust = 4, consol = TRUE, graph = FALSE)
hcpc_desc_var <- res_hcpc$desc.var
hcpc_payload <- list(
  clust = as.character(res_hcpc$data.clust$clust),
  data_clust_index = rownames(res_hcpc$data.clust),
  data_clust_columns = colnames(res_hcpc$data.clust),
  nb_clust = 4L,
  desc.var = list(
    test.chi2  = if (!is.null(hcpc_desc_var$test.chi2)) as.data.frame(hcpc_desc_var$test.chi2) else NULL,
    category   = if (!is.null(hcpc_desc_var$category))  lapply(hcpc_desc_var$category, as.data.frame) else NULL,
    quanti.var = if (!is.null(hcpc_desc_var$quanti.var)) as.data.frame(hcpc_desc_var$quanti.var) else NULL,
    quanti     = if (!is.null(hcpc_desc_var$quanti))     lapply(hcpc_desc_var$quanti, as.data.frame) else NULL
  )
)
write_json(hcpc_payload, file.path(out_dir("hcpc"), "decathlon_plain_k4.json"))
cat("[fixtures] hcpc/decathlon_plain_k4.json\n")

# ---- dimdesc / catdes / condes -------------------------------------------
desc <- dimdesc(res_pca, axes = 1:2, proba = 0.05)
desc_payload <- list()
for (k in seq_along(desc)) {
  axis_name <- names(desc)[k]
  d <- desc[[k]]
  desc_payload[[axis_name]] <- list(
    quanti = if (!is.null(d$quanti)) as.data.frame(d$quanti) else NULL,
    quali  = if (!is.null(d$quali))  as.data.frame(d$quali)  else NULL,
    category = if (!is.null(d$category)) as.data.frame(d$category) else NULL
  )
}
write_json(desc_payload, file.path(out_dir("dimdesc"), "pca_decathlon.json"))
cat("[fixtures] dimdesc/pca_decathlon.json\n")

# catdes on tea (Tea-time as target)
catdes_tea <- catdes(tea, num.var = which(names(tea) == "Tea"), proba = 0.05)
catdes_payload <- list(
  test.chi2 = if (!is.null(catdes_tea$test.chi2)) as.data.frame(catdes_tea$test.chi2) else NULL,
  category  = if (!is.null(catdes_tea$category))  lapply(catdes_tea$category, as.data.frame) else NULL,
  quanti.var = if (!is.null(catdes_tea$quanti.var)) as.data.frame(catdes_tea$quanti.var) else NULL,
  quanti     = if (!is.null(catdes_tea$quanti))     lapply(catdes_tea$quanti, as.data.frame) else NULL
)
write_json(catdes_payload, file.path(out_dir("catdes"), "tea_Tea.json"))
cat("[fixtures] catdes/tea_Tea.json\n")

# condes on decathlon with Points as the continuous target
condes_dec <- condes(decathlon, num.var = which(names(decathlon) == "Points"), proba = 0.05)
condes_payload <- list(
  quanti   = if (!is.null(condes_dec$quanti)) as.data.frame(condes_dec$quanti) else NULL,
  quali    = if (!is.null(condes_dec$quali))  as.data.frame(condes_dec$quali)  else NULL,
  category = if (!is.null(condes_dec$category)) as.data.frame(condes_dec$category) else NULL
)
write_json(condes_payload, file.path(out_dir("condes"), "decathlon_Points.json"))
cat("[fixtures] condes/decathlon_Points.json\n")

# condes on tea ~ age — exercises the quali + category branches (every Tea
# variable interacts with age in some way; many will be significant). Uses
# proba = 0.20 so we keep a richer cross-section than the default 0.05.
condes_tea_age <- condes(tea, num.var = which(names(tea) == "age"), proba = 0.20)
condes_tea_age_payload <- list(
  quanti   = if (!is.null(condes_tea_age$quanti)) as.data.frame(condes_tea_age$quanti) else NULL,
  quali    = if (!is.null(condes_tea_age$quali))  as.data.frame(condes_tea_age$quali)  else NULL,
  category = if (!is.null(condes_tea_age$category)) as.data.frame(condes_tea_age$category) else NULL
)
write_json(condes_tea_age_payload, file.path(out_dir("condes"), "tea_age.json"))
cat("[fixtures] condes/tea_age.json\n")

# dimdesc on PCA(decathlon) with a loose proba so quali / category are populated.
desc_loose <- dimdesc(res_pca, axes = 1:2, proba = 0.50)
desc_loose_payload <- list()
for (k in seq_along(desc_loose)) {
  axis_name <- names(desc_loose)[k]
  d <- desc_loose[[k]]
  desc_loose_payload[[axis_name]] <- list(
    quanti = if (!is.null(d$quanti)) as.data.frame(d$quanti) else NULL,
    quali  = if (!is.null(d$quali))  as.data.frame(d$quali)  else NULL,
    category = if (!is.null(d$category)) as.data.frame(d$category) else NULL
  )
}
write_json(desc_loose_payload, file.path(out_dir("dimdesc"), "pca_decathlon_proba50.json"))
cat("[fixtures] dimdesc/pca_decathlon_proba50.json\n")

cat("\ndone.\n")
