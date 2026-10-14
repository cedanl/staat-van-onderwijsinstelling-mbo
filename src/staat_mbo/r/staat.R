## Staat van de Onderwijsinstelling MBO zonder dashboard.
## Aanroep: Rscript staat.R <1cho_mbo.csv> <uitvoermap>
args <- commandArgs(trailingOnly = TRUE)
pad_1cho <- args[1]
uitvoer_basis <- args[2]
diplomasoorten <- Sys.getenv("STAAT_MBO_DIPLOMA")
soort <- Sys.getenv("STAAT_MBO_SOORT")

library(staat1cho)

basis <- maak_basisbestand(pad_1cho)
laatste_jaar <- max(basis$inschrijvingsjaar, na.rm = TRUE)
jaar <- laatste_jaar + 1L
uitvoer <- file.path(uitvoer_basis, jaar)
dir.create(uitvoer, recursive = TRUE, showWarnings = FALSE)
bewaar <- function(object, naam) {
  saveRDS(object, file.path(uitvoer, paste0(naam, "_", jaar, ".RDS")))
}

cohorten <- maak_instroom_cohort(basis, soort)
diploma <- maak_diploma_behaald(basis, diplomasoorten = diplomasoorten)
rendement <- bereken_rendement(cohorten, diploma, laatste_jaar = laatste_jaar)
uitval <- bereken_uitval(basis, diploma, cohorten, jaar)
wissel <- bereken_studiewissel(basis, cohorten, diploma, uitval)
indicatoren <- combineer_indicatoren(cohorten, rendement, uitval, wissel)

bewaar(basis, "Basisbestand1CHO")
bewaar(indicatoren, "Indicatoren_1cHO")
schrijf_benchmarkrapport(
  maak_benchmarkrapport(indicatoren),
  file.path(uitvoer, paste0("Benchmarkrapport_", jaar, ".xlsx"))
)
cli::cli_alert_success("Klaar. Uitvoer staat in {.path {uitvoer}}")
