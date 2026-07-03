import client from './client'

export const auditAPI = {
  // params: { entity_type, action, actor_id, date_from, date_to, limit, offset }
  list: (params) => client.get('/audit-logs/', { params }),
  entityTypes: () => client.get('/audit-logs/entity-types'),
}
