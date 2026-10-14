## Dashboard met mbo-voorstap: bronbestanden uploaden, samenvoegen, dashboard.
## smbo_samenvoegen() roept 'python -m staat_mbo samenvoegen' aan.

smbo_samenvoegen <- function(bestanden) {
  map <- tempfile("smbo_")
  invoer <- file.path(map, "invoer")
  uitvoer <- file.path(map, "uitvoer")
  dir.create(invoer, recursive = TRUE)
  ## Shiny noemt uploads 0.csv, 1.csv; het bestandstype hangt af van de naam.
  doelen <- file.path(invoer, basename(bestanden$name))
  file.copy(bestanden$datapath, doelen)
  log <- suppressWarnings(system2(
    Sys.getenv("STAAT_MBO_PYTHON"),
    c("-m", "staat_mbo", "samenvoegen", shQuote(doelen), "--uitvoer", shQuote(uitvoer)),
    stdout = TRUE,
    stderr = TRUE
  ))
  status <- attr(log, "status")
  meldingen_pad <- file.path(uitvoer, "meldingen.txt")
  meldingen <- if (file.exists(meldingen_pad)) {
    readLines(meldingen_pad, encoding = "UTF-8")
  } else {
    c("Niet gelukt.", utils::tail(log, 5))
  }
  list(
    ok = is.null(status) || status == 0,
    pad = file.path(uitvoer, "1cho_mbo.csv"),
    meldingen = meldingen
  )
}

if (Sys.getenv("STAAT_MBO_ALLEEN_FUNCTIES") != "1") {
  ## Vaste poort zonder browser, voor opnames en tests.
  poort <- Sys.getenv("STAAT_MBO_POORT")
  if (nzchar(poort)) {
    options(shiny.port = as.integer(poort), shiny.launch.browser = FALSE)
  }
  staat1cho::start_dashboard(
    voorstap = list(
      titel = "Staat van de Onderwijsinstelling MBO",
      uitleg = paste(
        "Kies al je RO- en TBG-i-bestanden tegelijk, of de uitvoer van",
        "mbo-bekostiging-bestanden (datamodel of zip). Klik dan op Samenvoegen."
      ),
      samenvoegen = smbo_samenvoegen
    ),
    diplomasoorten = Sys.getenv("STAAT_MBO_DIPLOMA")
  )
}
