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


def migrate_relationships(self):
    """
    Migrate relationships to the relationship collection.
    
    """
    from crits.relationships.handlers import forge_relationship

    failed_rels = []
    old_relationships = getattr(self.unsupported_attrs, 'relationships', None)

    if old_relationships:
        for rel in old_relationships:
            rel_type = rel.get('relationship', None)
            date = rel.get('date', None)
            relationship_date = rel.get('relationship_date', None)
            right_id = rel.get('value', None)
            right_type = rel.get('type', None)
            rel_confidence = rel.get('rel_confidence', 'unknown')
            rel_reason = rel.get('rel_reason', None)
            rel_anaylst = rel.get('analyst', None)
            
            result = forge_relationship(class_=self,
                                        right_id=right_id,
                                        right_type=right_type,
                                        date=date,
                                        rel_type=rel_type,
                                        rel_date=relationship_date,
                                        rel_confidence=rel_confidence,
                                        rel_reason=rel_reason,
                                        rel_analyst=rel_anaylst,
                                        migrate=True)
            if not result['success']:
                if result['message'] != "Relationship already exists.":
                    failed_rels.append(rel)
        # If the migration was not successful, keep the relationship in unsupported_attrs.
        if failed_rels:
            self.unsupported_attrs.relationships = failed_rels
        else:
            del self.unsupported_attrs.relationships