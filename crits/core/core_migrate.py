# In the event of a migration that applies to multiple TLOs, you can put
# functions here so you don't have to duplicate code across several migration
# files.

# For migrating analysis results to their own collection.
# mgoffin
# 2014-09-24
def migrate_analysis_results(self):
    from crits.services.analysis_result import (AnalysisResult,
                                                AnalysisConfig,
                                                EmbeddedAnalysisResultLog)
    old_results = getattr(self.unsupported_attrs, 'analysis', None)
    if old_results:
        for result in old_results:
            ar = AnalysisResult()
            ar.analysis_id = result.get('id')
            if ar.analysis_id:
                del result['id']
            config = result.get('config', {})
            ar.config = AnalysisConfig(**config)
            if 'config' in result:
                del result['config']
            logs = result.get('log', None)
            if logs:
                for l in logs:
                    le = EmbeddedAnalysisResultLog(**l)
                    ar.log.append(le)
                del result['log']
            ar.merge(arg_dict=result)
            ar.object_type = self._meta['crits_type']
            ar.object_id = str(self.id)
            ar.save()
    try:
        del self.unsupported_attrs['analysis']
    except:
        pass
