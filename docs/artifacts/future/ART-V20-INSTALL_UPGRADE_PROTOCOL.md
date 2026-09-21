# ART-V20-INSTALL-JOURNEY / UPGRADE-ROLLBACK protocol

Status: drafting
Target: V2.0
Owner: ChatGPT lead

## Clean-install requirements

Start from:
- empty checkout/environment;
- no prior var/ database/artifacts;
- no user credentials copied from developer machine;
- no demo project/token/provider activity.

Steps must be scripted/documented:
1. install dependencies/build artifacts;
2. create/generate install-local identity and required local secrets;
3. configure database without known default password;
4. migrate to head;
5. start API + console;
6. verify health/ready;
7. observe honest empty/unconfigured state;
8. create a real local project;
9. optionally configure a permitted local route;
10. execute one supported local mission;
11. export a secret-safe support bundle.

Fail if missing required secrets/config cause silent mock mode.

## Upgrade

Freeze:
- old version SHA/schema;
- DB backup;
- artifact manifest;
- project/mission IDs;
- knowledge/extension config.

Upgrade:
1. stop/drain writes;
2. backup;
3. install new code/deps;
4. migrate DB;
5. integrity check;
6. start in protected mode;
7. reopen prior project/mission/artifact;
8. run smoke;
9. enable normal writes.

## Rollback

Default rollback strategy for data-changing migrations:
- restore validated pre-upgrade backup into clean target;
- do not assume every Alembic downgrade is lossless.

If a migration explicitly supports downgrade, test it separately.

Record:
- rollback support per migration;
- data-loss risk;
- restore time;
- schema/config compatibility.

## Required negatives

- existing developer .env absent;
- fixed known DB password rejected;
- incompatible extension disabled/refused;
- failed migration leaves old backup untouched;
- partially migrated DB does not start writable;
- old binary against newer incompatible DB fails closed;
- support bundle contains no secret values/private browser state.

## Ownership

Session A:
- database/migration/backup/startup/runtime pieces.

Session B:
- install CLI/docs/support bundle/extension compatibility/operator journey.

Session A integrates shared CLI/API surfaces.
