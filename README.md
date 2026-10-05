# AI-Decisional-Tree

Dataset loading uses `kagglehub` and writes extracted files to the configured
`Dataset.extract_path`, resolved relative to the application directory.
Completed downloads are reused through kagglehub's completion markers;
metadata requests may still require network access. `DataLoader.load_data()`
returns the resolved dataset directory. The legacy `download_path` and
`archive_name` settings are no longer used by the loader.

If HTTPS certificate verification fails, the download is retried once after
`truststore` enables the system certificate store. TLS verification remains
enabled. This changes SSL configuration for the application process; any
retry failure is propagated to the caller.