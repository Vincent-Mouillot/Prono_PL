if (!requireNamespace("rprojroot", quietly = TRUE)) {
  install.packages("rprojroot")
}

library(rprojroot)

root <<- rprojroot::find_root(rprojroot::has_dir("Prono_PL"))

source(file.path(root, "Prono_PL", "get_calendrier.R"))

source(file.path(root, "Prono_PL", "get_all_data.R"))

source(file.path(root, "Prono_PL", "get_classement.R"))