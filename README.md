# Entsorgungskalender - Karlsruhe

Fetch the dates for trash pickups for the city of Karlsruhe, Germany

Our beautiful city sadly doesn't have an easy way of getting the pickup dates for the various types of trash.
Additionally, the dates are not very easy to remember or very regular. This python application is intended as a backend
for a more complex service, use `Postgresql` as a database to store users and future dates.

Without the database, this application is useless for you. If you just need the dates for your street, either use this
code as a base for your own crawler or use the telegram bot this was created for.

For more information, see ....

---

# Environment Variables

Add these variables to connect to the PostgreSQL database:

| Key               | Default  | Description                              |
|-------------------| :------: |------------------------------------------|
| POSTGRESQL_HOST   |          | Address the database can be reached with |
| POSTGRESQL_USER   | postgres | Username for the database                |
| POSTGRESQL_DB     | postgres | Name to use for the database             |
| POSTGRESQL_SECRET |          | Password for PostgreSQL                  |
| POSTGRESQL_PORT   |   5432   |

