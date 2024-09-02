library(taskscheduleR)

taskscheduler_create(
  taskname = "get_updated_classement", 
  rscript = "C:/Users/vmoui/OneDrive/Bureau/Prono_sport/get_classement.R",
  schedule = "DAILY",
  starttime = "08:02"
)

# taskscheduler_delete("get_updated_classement")

taskscheduler_create(
  taskname = "get_updated_stats", 
  rscript = "C:/Users/vmoui/OneDrive/Bureau/Prono_sport/get_all_data.R",
  schedule = "DAILY",
  starttime = "08:19"
)

# taskscheduler_delete("get_updated_stats")