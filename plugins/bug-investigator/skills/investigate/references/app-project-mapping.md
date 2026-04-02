# App → Project Reference

Use this mapping to ensure subagents query the correct project for the affected app.

## Mixpanel

"Staging" projects correspond to the `dev` deployed environment. Use the production project for production bugs; use the staging project for dev environment queries.

| App                        | Production Project ID | Dev/Staging Project ID |
| -------------------------- | --------------------- | ---------------------- |
| Compass (Caregiver Portal) | 2827696               | 2741167                |
| Admin Portal               | —                     | 2741147                |
| Atlas                      | 3206888               | 3200745                |
| Member Portal (Cherrim)    | 1880877               | 1880873                |

Note: Access to some projects may be restricted. If a query fails due to permissions, flag it as `[REQUIRES USER ACTION]` and provide the query for the user to run manually.

## LaunchDarkly

| App                        | Project Key                                                       |
| -------------------------- | ----------------------------------------------------------------- |
| Caregiver Portal (Compass) | `cargiver-portal` _(intentional spelling — this is the real key)_ |
| Member Portal (Cherrim)    | `default`                                                         |
| Admin Portal               | `admin`                                                           |
| Atlas                      | `atlas`                                                           |
| Alba — backend             | `alba-backend`                                                    |
| Alba — Flutter             | `alba-flutter`                                                    |
| EHR API                    | `ehr-api`                                                         |
| Rotom (backend)            | `rotom`                                                           |
