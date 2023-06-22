class BucketFuzzers:
    @staticmethod
    def _get_data(fuzzer_id, fuzzer_rev, data_type, ext=""):
        return f"{fuzzer_id}/{fuzzer_rev}/{data_type}{ext}"

    def __init__(self, name: str):
        self.name = name

    def binaries(self, fuzzer_id, fuzzer_rev, ext=".tar.gz"):
        return self.name, self._get_data(fuzzer_id, fuzzer_rev, "binaries", ext)

    def seeds(self, fuzzer_id, fuzzer_rev, ext=".tar.gz"):
        return self.name, self._get_data(fuzzer_id, fuzzer_rev, "seeds", ext)

    def config(self, fuzzer_id, fuzzer_rev, ext=".json"):
        return self.name, self._get_data(fuzzer_id, fuzzer_rev, "options", ext)

    def fuzzer_dir(self, fuzzer_id):
        return self.name, fuzzer_id

    def revision_dir(self, fuzzer_id, fuzzer_rev):
        return self.name, f"{fuzzer_id}/{fuzzer_rev}"


class BucketData:
    @staticmethod
    def _get_data(fuzzer_id, fuzzer_rev, data_type, result_id, ext=""):
        return f"{fuzzer_id}/{fuzzer_rev}/{data_type}/{result_id}{ext}"

    def __init__(self, name: str):
        self.name = name

    @staticmethod
    def _get_grouped_logs(fuzzer_id, fuzzer_rev, grouped_by, date, ext):
        return f"{fuzzer_id}/{fuzzer_rev}/logs/grouped/{grouped_by}/{date}{ext}"

    def merged_corpus(self, fuzzer_id, ext=".tar.gz"):
        return self.name, f"{fuzzer_id}/corpus{ext}"

    def corpus(self, fuzzer_id, fuzzer_rev, result_id, ext=".tar.gz"):
        return (
            self.name,
            self._get_data(fuzzer_id, fuzzer_rev, "corpus", result_id, ext),
        )

    def logs(self, fuzzer_id, fuzzer_rev, result_id, ext=".tar.gz"):
        return (
            self.name,
            self._get_data(fuzzer_id, fuzzer_rev, "logs", result_id, ext),
        )

    def crash(self, fuzzer_id, fuzzer_rev, input_id):
        return (
            self.name,
            self._get_data(fuzzer_id, fuzzer_rev, "crashes", input_id),
        )

    def logs_grouped_daily(self, fuzzer_id, fuzzer_rev, date, ext=".tar.gz"):
        return (
            self.name,
            self._get_grouped_logs(fuzzer_id, fuzzer_rev, "daily", date, ext),
        )

    def logs_grouped_monthly(self, fuzzer_id, fuzzer_rev, date, ext=".tar.gz"):
        return (
            self.name,
            self._get_grouped_logs(fuzzer_id, fuzzer_rev, "monthly", date, ext),
        )

    def fuzzer_dir(self, fuzzer_id):
        return self.name, fuzzer_id

    def revision_dir(self, fuzzer_id, fuzzer_rev):
        return self.name, f"{fuzzer_id}/{fuzzer_rev}"
