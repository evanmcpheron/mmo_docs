# MASTER PROMPT — Create the Complete RPG: Living World 2D MMO Development Guide

> **Audience:** The AI/engineering agent responsible for *creating the actual documentation repository*. Read this entire prompt, every supplied companion document, the original `game_docs` repository, and both input ZIP archives before producing the new guide. This is a file-generation assignment, not a request for a design brainstorm, a short plan, Unreal gameplay code, or a claim that a game already exists.
>
> **Unifying promise:** **A player who logs into a quiet server alone can pursue the complete PvE adventure, develop the world, and progress a chosen multi-activity profession. When more people arrive, the same world offers valuable cooperation, not new mandatory dependencies.** Combat, professions, exploration, settlement development, and social play are connected parts of one game.

## 0. Assignment, source materials, and required deliverable

Assume the roles of senior 2D MMORPG creative director, technical game designer, Unreal Engine 5.8.3 C++/Blueprint engineer, Paper2D/PaperZD technical artist, network engineer, gameplay economy designer, persistence/backend architect, technical writer, tool-builder, and QA lead. Your audience is a developer learning Unreal; teach exact practical steps and explain why they matter, without inventing working code or claiming tests that have not run.

**Working title:** `RPG`. **Genre:** original high-fantasy, top-down/three-quarter-view, **entirely 2D** persistent-world action MMORPG designed initially for **1–30 concurrent players in a realm/zone test population**, with architecture that can evolve only after measurement. Player sprites, NPCs, creatures, world tiles, props, decorations, and effects are **2D**. There is **no 3D environment, 2.5D terrain, 3D mesh art pipeline, 360-degree 3D walk simulation, rotating camera, or 3D billboard-character requirement**. Optional engine Z/layer use for implementation convenience does not change the 2D visual or movement design.

Use these source materials, in this order:

1. The design commitments in **this prompt** and the companion `DESIGN_DECISIONS.md`, `SOLO_TO_30_DESIGN_AND_TESTS.md`, and `FEATURE_COVERAGE.md`.
2. The actual supplied `2d_game_assets.zip` and its creator-authored guides, plus the companion `ASSET_AUDIT.md` and `ASSET_INVENTORY.csv` as *preliminary inventory evidence*. Recheck the archive paths, animation conventions, sprite layering, and licenses; never assume an unprovided visual exists.
3. The attached **`Plugin+-+Unreal+Engine+5.zip`**, which contains the `MultiplayerSessions` source plugin. Read its exact version, `.uplugin`, module dependencies, C++ methods, menu, and Blueprint content. Read `MULTIPLAYER_PLUGIN_AUDIT.md` before relying on it.
4. Existing structural reference: `https://github.com/evanmcpheron/game_docs` (`main`), including `README.txt`, `AGENTS.md`, overview/architecture, 12 historical phases, 19 system chapters, 163 currently registered asset pages, per-asset contracts, C++ engineering standard, source manifests, generation scripts, interactive checklists, and offline search. **Reference the documentation practices, not the platformer game design.**
5. The actual installed Unreal Engine 5.8.3 source/docs and installed PaperZD/plugin versions, where accessible. Official docs establish engine behavior; third-party source establishes plugin behavior. Uninspected or uncompiled behavior must remain explicitly unverified.

**Create a new documentation repository**, tentatively `RPG_2D_Living_World_Development_Guide`. Do not overwrite, rewrite, force-push, or delete the existing `game_docs`. If you can create a remote repository, obtain separate approval for that external publication action; otherwise create a local directory and distributable ZIP. Keep both user-supplied ZIPs separate from the published documentation package. **Do not redistribute paid sprite art, third-party plugin source/binaries, or unlicensed previews in a public repository.** Source-relative references, hashes, allowed metadata, import instructions, compatibility tables, and original documentation diagrams are fine.

**Deliver** a real, fully linked, offline HTML documentation site; not a summary or website mockup. `index.html` must open directly from disk (`file://`), with relative navigation, search, phase progress, asset search, system chapters, dependency maps, glossary, technical reference, testing instructions, source registries, reproducible generation tools, and a ZIP containing the entire new repository. It is a **build manual** for a future Unreal game. **Do not create any `.uproject`, `.uasset`, `.umap`, runtime C++ implementation, executable, database instance, dedicated-server binary, or fictional passing Unreal test.** Illustrative, labeled pseudocode and example API signatures inside docs are permitted.

Produce the whole manual through verifiable batches if output is large; do not silently omit features or mark incomplete work complete. The final answer must include actual file paths, counts, static validation results, known gaps, and what was not runtime-tested.

## 1. Non-negotiable gameplay/design principles

1. **Balanced pillars.** Combat progression, world development, exploration, gathering/crafting, and MMO social play matter comparably. A feature should create an interaction with at least one other pillar, without every player being forced into every system.
2. **Dynamic chosen professions.** At character creation, selecting exactly **one primary vocation is required**. A vocation is a connected *adventuring lifestyle* containing complementary activities, challenges, missions, and creative decisions—not a job consisting of clicking one resource node repeatedly. See Section 4 for the five starting vocation designs and the changing-vocation policy.
3. **Enjoyable at population 1, better connected at 30.** No mandatory group sizes, social trades, player-only services, server population thresholds, raid-only items essential to main progression, uncontestable rare spawns, or unreachable community projects. Implement solo-completable variants and capable, limited NPC help where encounters need multiple roles. Human cooperation adds efficiency, variety and community recognition, not access to the actual game.
4. **Living Regions.** Player actions affect persistent settlement development, regional danger, exploration discoveries, NPC dialogue/services, safe routes, resource opportunities, and events. Changes are visibly staged, deterministic, testable and reversible only where specifically authored. Do **not** build unrestricted player-driven terrain modification or a universal simulated ecosystem.
5. **Adventures, not repetitive chores.** Each vocation supports short varied loops containing decisions, discoveries, danger, problem-solving, action and meaningful results. Do not use compulsory daily logins, idle timers, excessive passive waiting, time-gated story progress, punitive offline decay, or repetitive clicking as the main leveling mechanism.
6. **Familiar RPG foundation.** Character progression, exciting combat, items, rarity, talents, quests, vendors, social systems, and dungeons should be understandable. Distinctiveness comes from how the pillars interact, not inventing opaque versions of every standard RPG system.
7. **Server is authoritative.** Clients never award items/XP/money, complete world projects, roll loot, accept trades, or finalize quests. The authoritative server/service validates the request, commits durable state once and then replicates projections to clients. Client visuals and PaperZD animation do not grant rewards.
8. **C++ rules, Blueprint authoring.** Stable gameplay invariants, authority, transactions, networking, persistence, and reusable components are C++. Provide meaningful `BlueprintReadOnly`/`BlueprintCallable`/`BlueprintImplementableEvent`/editable Data Asset extension points as appropriate, with explicit limits: editing a property is not permission to bypass server validation.
9. **No art fiction.** Use the character sprites and paper-doll layers actually supplied; document absent tilesets, 8-direction angles, costumes, actions, creatures, FX, and animations as real tasks with compatibility fallbacks. Initial four-direction playback must be a genuine supported baseline.
10. **Small end-to-end steps.** Follow the original `game_docs` philosophy: create → compile → configure → connect previous assets → place something in a test map → run → verify acceptance and rejection → regress. Build a minimal complete experience before increasing content or speculative MMO infrastructure.
11. **Original fantasy setting.** Capture a grounded atmosphere of ancient paths, guarded settlements, forests, mountains and ruined strongholds; invent original world, place names, history, factions and stories. Do not copy Tolkien's character names, geographic names, maps, narratives, dialogue, trademarked product branding or distinctive designs.
12. **No exploit-based fun.** Shared worlds, random spawns, economies and projects need grief prevention, concurrency safety, anti-duplication, moderation, recovery, accessibility and graceful failure from their first implementation.

Design claims must be labeled **Committed requirement**, **Recommended initial choice**, **Tuning example**, **Deferred extension**, or **Unverified integration**, where ambiguity could mislead a beginner.

## 2. Source repository migration: what remains and what changes

The original `game_docs` is a documentation-only manual for a 2D side-scrolling exploration/platforming RPG targeting UE 5.8.3 and PaperZD. Its guide currently has 12 phases, 19 system chapters, and 163 documented planned assets. None of those pages proves an Unreal project compiles. Its historical architecture uses X/Z motion with a Y-plane constraint, `BP_PlayerProfile` and `BP_WorldState` as local session models, `BP_GameInstance` as travel/save coordinator, normal single-player `SaveGame` generations, six equipment slots, no formal quests, no merchants, no crafting, no random loot, and no multiplayer.

**Reuse:** explicit state ownership; definitions vs runtime instances; immutable authored data; UI/animation as observers; event-driven update; stable IDs; checked transactions; readable engineering conventions; individual asset pages; creator-friendly folder mirrors; generated site indices; reversible saved progress; integration-focused phases; real success/failure tests.

**Replace rather than copy:**

- Side-scrolling jump/ledge/coyote/platformer-centered movement → **top-down 2D eight-way movement input**, initially represented using four available animation directions, with no climbing/platformer traversal assumptions. **Sprint, dodge, a short server-validated top-down hop/jump, and swimming** remain committed mechanics from the prior game brief, but must be adapted for an entirely 2D world. They require collision/action eligibility rules and honest placeholder art where the archive lacks animations, not platformer precision-jump physics.
- Side camera / 3D perspective → **fixed orthographic/elevated 2D camera**, no rotation, user-adjustable bounded zoom, carefully managed tile and sprite draw order.
- 3D terrain/biome meshes/landscape/3D NavMesh → **2D tilemaps, layered authored zones, collision tiles, 2D pathing/navigation adapted to the chosen Unreal setup**, safe walkable regions, line of sight, occlusion and foot-position-based Y-sort.
- Local-only profile and world owner → **server-authoritative character state + backend durable store; separate persistent realm/region facts; runtime server Actors as projections**. The GameInstance is not a cross-server database or shared-world coordinator.
- Single-player save file as MMO truth → **idempotent server-side storage, transactional ledger/receipts, versioned records, reconnect and restart recovery**.
- Whole-server ordinary level travel → **per-character biome transfer**, leaving other connected players in their zone; zone handoff tickets/validation where separate zone servers are used.
- Simple item/inventory/skills → rich gear, visible paper-doll compatibility, rarity/affixes, loot tables, profession crafting, talents, character/account identity.
- Dialogue-only NPCs → authored dialogue, services, branching quests, dynamic world reactions.
- Fixed map objects → bounded randomized gathering sites, fishing pools, farms, persistent constructions and region-event states.
- No networking → supplied session plugin audited and bounded; authoritative remote multiplayer, reconnect, persistence, and solo-to-30 quality built into the design.

Create an explicit `architecture/source-migration.html` crosswalk: **old asset/system → new recommended owner → preserve/replace/deprecate → exact rationale → dependencies → migration art implications → implementation risks**. Preserve the original documentation as **historical reference**, not as the new game's canonical asset manifest, phase schedule or verified code.

## 3. World presentation, movement and 2D content pipeline

### 3.1 Fixed viewpoint and movement

- Camera: fixed **three-quarter top-down pixel-art view**, no manual rotation. Bounded zoom in/out with consistent pixels-per-unit, legible gameplay space, configurable scroll/smoothing, UI unaffected by world zoom. Choose the technically simplest Paper2D/orthographic arrangement that preserves sprite quality; compare alternatives only where there is an actual tradeoff.
- World: top-down/three-quarter-view **2D tile layers**, collision and obstacle layers, overdraw elements (trees/roofs/archways), interior transitions, paths, roads, water edges, bridges represented by tiles/layers, and authored visual states for constructed structures. No 3D models required. Document Paper2D TileSet/TileMap or a verified, justified alternative; avoid claiming a TileMap feature that the installed version cannot perform.
- Physical input: eight-way directional movement on the 2D play plane (normalized diagonal speed), walk/sprint, short dodge, **short hop/jump over specifically marked low 2D obstacles**, swimming in authored eligible water, interaction, attacks, fishing cast/reel, tile-safe collision, pathfinding for creatures and helpers, and deliberate directional sprite selection. Jump is an explicit gameplay state/short timed hop with server collision/landing validation, **not a precision side-view platformer jump**. Swimming has server-authorized water-enter/exit and movement/ability rules. The supplied sprite archive must be audited for hop/swim art; missing poses use clearly labeled temporary animations until replacement art is authored. There is **no climbing**.
- Animation: start with real **four-facing** sprites. Support input/velocity direction in eight sectors internally and project onto nearest available art direction by an explicit, stable mapping; never imply the four current sprites have true eight-direction angled frames. Stage a future eight-direction paper-doll/weapon animation art matrix and safe compatibility/version migration.
- Render order: feet/Y-based occlusion, vegetation/canopy/roof separation, layer-specific draw-order offsets, animation pivots, transparent gaps, sprite texture filtering, pixel scaling, ambient weather/day-night tints, emissive/lighting as viable in 2D. Avoid depth pop/character clipping and cosmetic transforms affecting hitboxes.
- Controls: keyboard/mouse and controller; optional click-to-move only if justified as a separate control path with pathfinder and anti-cheat design. Document screen-space targeting and server-range/LOS checks for both input devices.

### 3.2 Art archive audit and compatibility

Audit `2d_game_assets.zip` by exact content paths, sheets, guide text, file provenance, dimensions, directions, animation pages, palette variants, layer identifiers, weapon/action compatibility and license restrictions. Existing inspected evidence indicates original Mana Seed-style packs with `p1` locomotion, `p2` farming/mining/woodcutting, `p3` fishing and `p4` other actions; visual layers such as `0bas`, `1out`, `2clo`, `4har`, `5hat`, `6tla` and `7tlb`. Verify directly from the archive before documenting a particular sprite.

Produce at minimum:

- Per-file metadata inventory (or validated reuse of companion `ASSET_INVENTORY.csv`), archive hash, source folder, author docs, sprite frame dimensions and import settings where real.
- **Appearance matrix:** body variants × hairstyles × headwear × outfits × cloaks × tools/weapons × animations × four initial facings. Mark support as verified from asset sheets, placeholderable, requires authored art, or unsupported. Gameplay slot `Chest` is the same as legacy `Top`; `Legs` is legacy `Pants`. Full logical equipment does **not** guarantee individual overlay art for every equipment slot.
- **Action matrix:** idle, move, sprint (fallback policy), combat poses (sword/shield, bow, spear, dual blades), hit/death (verify), gathering/mining/woodcutting, farming, fishing cast/wait/reel/catch, crafting (forge/cook/alchemy), dodge, top-down jump/hop, swim/water traversal, quest interactions, and NPC idle/walk; map each to actual source page/pose or a clearly labeled art requirement.
- **Terrain gap matrix:** the supplied ZIP is principally character/equipment/action art. Do not claim it contains a complete biome environment tileset, mining rocks, growing trees, water tile animations, buildings, monster sprites, VFX or UI assets unless the exact archive paths prove it. Catalog additional Seliel-compatible assets separately as unacquired until the user provides them and license terms are checked.
- **PaperZD adaptation:** Paper2D for sprites, TileSets/TileMaps, Flipbooks, environmental loops; PaperZD for character state/sequence/notifies if verified in installed release. Layered equipment follows shared pose/time without duplicating gameplay action logic; no plugin animation notify is the authoritative source of combat or loot.
- **Import instructions:** exact Editor operations for texture compression/filter settings, pixel art scaling, sprite extraction, pivots, atlas considerations, layer sync, blueprints/data references, asset migrations, remote-player facing, equipment preview and regression after eight-direction expansion.

Never redistribute the original paid sprites/plugin. Never substitute invented screenshots for verifiable art.

## 4. Required vocation selection and integrated profession system

### 4.1 A profession is an adventure loop, not an occupation

**Every playable character must select one primary vocation during character creation.** The choice defines their signature multi-system loop, starter skills/recipes/tools, NPC mentors, profession quests, specialization graph, ways to contribute to regions, distinct useful products, cosmetic identity (using actual supported art only), and reputation in the world. Each vocation must have **at least three different moment-to-moment interaction types**, including an outing/exploration or risk element and an authored decision that affects the result. Gathering-only or crafting-only advancement is prohibited as the main path.

**Recommended five vocations (canonical design targets):**

| Primary vocation | Connected activities, not isolated jobs                                                                                                                                            | Meaningful adventure decisions and world impact                                                                                                                  |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Forgekeeper**  | Prospect and mine ore → scavenge/salvage ruins → refine and forge weapons/tools/armor → repair defensive structures → escort or defend supply expeditions                          | Search for rare veins, select alloys and forging techniques, recover lost plans, determine whether material goes to improved equipment or rebuilding settlements |
| **Hearthkeeper** | Fish → tend small farms/gardens → forage culinary ingredients → cook and bake expedition food → provision NPCs and players → support seasonal village events                       | Choose seasonal recipes, plan food for changing dangers/weather, investigate fish migrations, rescue damaged fields and feed threatened settlements              |
| **Wayfinder**    | Explore unknown trails → map landmarks → track rare creatures and hostile camps → fight as scout/skirmisher → recover artifacts → share or sell authorized discoveries             | Interpret clues, choose safe/fast/dangerous routes, unlock shortcuts, report emerging threats, lead expeditions and expose hidden resource areas                 |
| **Woodwright**   | Explore forests → fell mature eligible trees → replant/restore groves → saw/craft furniture, bows, traps and supports → build watchposts/bridges → defend forest routes            | Choose sustainable harvest areas, identify quality timber, fortify regional projects, investigate corrupted groves and adapt traps to enemy behavior             |
| **Apothecary**   | Explore and identify plants/fungi → collect reagents → study creature/environment effects → prepare salves/tonics/antidotes → heal/support expeditions → resolve local afflictions | Decide formula tradeoffs, find rare reagents during hazardous expeditions, cure regional problems and supply combat groups                                       |

The exact names are editable lore labels; **the combined gameplay responsibility is not optional**. To avoid claiming unfinished features as playable, the early closed prototype can expose only the fully integrated vocations (start with Forgekeeper, Hearthkeeper, Wayfinder); the final guide must specify implementation of **all five** before complete-system acceptance. All five need playable starting routes and end-to-end verification, not decorative tooltips. If archival art does not exist for an Apothecary action, author an explicit fallback with an art-production task.

### 4.2 Profession choice must be meaningful without being a trap

- The chosen primary vocation specializes the character in tasks and rewards, but **every player can fight, take quests, explore, harvest common materials, fish at basic spots, obtain basic survival supplies, and use NPC services**. Specialized production, lore discoveries, advanced techniques, superior outcome control and vocation quest chains belong to the chosen vocation.
- Provide independent **combat disciplines** (suggest Vanguard, Ranger, Arcanist and Warden) so a fisherman can also be a frontline warrior or a healer, and a scout can wield a bow or magic. Combat specialization is independent of vocation; choose a starting combat discipline during the introduction or in the creator only if UX testing favors it. Each combat discipline gets documented skill trees and intended roles, but none is a mandatory solo content gate. Start with art-supported weapon types and openly stage animation gaps for magic/healing.
- The vocation selection screen must communicate **typical actions, difficulty/tempo, end products, contribution to the world, combat synergy, strengths and boundaries**. Preview character appearance and real supplied paper-doll layers; avoid misrepresenting generic clothing as vocation-exclusive sprites.
- Allow a **rare, intentional, server-validated vocation change** at an appropriate trainer after an introductory commitment window. Document exact policy for accumulated XP, previously learned recipes, retained items, profession-locked abilities, transition costs and cooldowns. This prevents permanent mistakes; do not create an exploit that lets players cheaply bypass every specialization.
- Multiple character slots may offer another chosen vocation. No player is required to maintain alts. Long-term achievement, regional contribution and critical quest progress may never assume a second character.
- Provide **base proficiency** in common tasks with weaker outputs/advanced access than specialists; offer **NPC alternative production services** with fair costs for goods otherwise gated behind other vocations. Nobody should need a dedicated human blacksmith online to finish the story or prepare for a dungeon.
- Profession skill trees should include meaningful activity improvements such as better evaluation, branching recipes, safer expedition options, situational crafting decisions and unique traversal/discovery interaction—not merely +1% yield repeated 50 times.

### 4.3 Dynamic vocation session design

For **every vocation**, document at least:

1. One accessible **5–10 minute short-session loop** that contains movement and at least two different activity types; pacing figures are **targets to test**, not facts.
2. One **15–30 minute expedition loop** with a risk/reward decision, an encounter, discovery or timed ecological condition, and an authored purpose.
3. One **long-term mastery pursuit** tied to regional projects, advanced recipes/gear, collections, discoveries or important repeatable challenges.
4. One **combat connection** (equipment, temporary preparation, tracking, area defense, support or enemy weakness discovery) and one **noncombat route** for players who prefer calmer sessions.
5. The ability to achieve each mandatory milestone **entirely alone**, including obtaining required ingredients, completing project contributions, and progressing recipes without external human trades.
6. A path to contribute to shared settlement development, regional safety and discoveries in ways proportionate to the activity—not by forcing everybody to donate interchangeable currency.
7. Contracts and events that vary objectives, locations, obstacles and outcomes; use authored and weighted variation, not unlimited procedural story claims.
8. Player choice and failure states: damaged tool, wrong ore grade, incomplete recipe, fish escaping, crop weather event, incorrect route, exhausted resource site, interrupted expedition, full inventory, disconnected client.
9. Solo proof, two-client cooperative proof, and 30-player contention/performance proof with clearly distinguishable expectations.
10. Separate authored **vocation level/mastery**, combat level and world reputation. None is silently inferred from animations or number of clicks.

Avoid skill checks that are inaccessible to disabled players: timed fishing input needs an accessible alternate mode, configurable timing and controller parity. Provide accessibility-safe outcomes without allowing the client to award the catch.

## 5. Living Regions: persistent shared development, threat, discovery

**Living Regions are the game's signature interaction system.** A region is a bounded, versioned unit of authored content with mutable, server-authoritative projections of three main axes:

1. **Settlement Development**: a small authored set of visible building/road/bridge/watchtower/service stages, initialized in a viable starter state. Player contributions fulfill named construction objectives with appropriate materials, rescue missions, exploration records or combat achievements. Completion changes tiles/props, NPC schedules/services, routes, dialogue, vendors, map and quest options. Different professions may contribute different eligible categories. Projects must make sense in story and cannot require any single player vocation.
2. **Regional Danger**: authored enemy camps, hostile patrols, lairs, trade disruption, threat bands and event triggers, not fully emergent machine-driven ecology. Players may investigate, repel or resolve threats. Danger responds to approved server events with bounded decay/reset policies. Distinct encounter stages and readable threats, not simply increasing enemy health.
3. **Regional Discovery**: hidden trails, ruins, lore, resource pockets, fish habitats, cartographic entries, safe passages and named exploration landmarks. Distinguish **personal discovery** (one character's journal) from **shared discoveries** (server realm state) and a discovery available to all after milestone completion. Don't let first-arrival explorers permanently monopolize meaningful progress.

### 5.1 Concrete example: The Elderwood Frontier

A frontier village's northern road is disrupted by hostile creatures. A Wayfinder discovers tracks and a hidden route; a Forgekeeper retrieves ore/salvage, forges reinforced fittings and joins a caravan defense; a Hearthkeeper gathers food, fishes for supplies and feeds expedition volunteers; a Woodwright produces bridge timbers and protective barriers; an Apothecary creates a field remedy and investigates blighted flora. Enemy pressure decreases after a genuine encounter; the newly repaired bridge opens a **visually authored path** and an NPC merchant service; the next regional quest arc unlocks. One solo player can satisfy every essential milestone through personal quests, available base skills, earned NPC aid or an alternate project objective. A 30-player realm offers simultaneous activities, specialization and recognition, without imposing 30-player quotas on an isolated player.

### 5.2 Persistent-world implementation contract

For every project, region event and construction state, document:

- Stable `RegionId`, `ProjectId`, `StageId`, `ObjectiveId`, `ContributionId` and server-authoritative `Revision` or equivalent canonical identity; authored definitions separate from persisted counters, completion receipts and runtime actors.
- Exact authored stages and tilemap/prop/passage variants. Runtime presentation reads stage; it does not permanently rewrite source tiles or grant success from its own animation finish.
- Supported contribution sources, validation, per-character receipts, anti-spam/anti-dupe policies, idempotency keys, resource deductions and transactional world progression, plus project version migration.
- Condition/activation rules for town growth, vendor availability, route unlocking, dialogue, quests, minimap and NPC behavior. State updates must be observable to players joining mid-stage.
- Rules for inactivity, overnight server downtime, server restarts, new realms, region reset, event failure and authored reactivation. **Never roll back major permanent construction just because players logged out.** Repeatable threats need bounded, transparent renewal without punishing absence.
- Meaningful contributions from all vocations and non-specialists, without a hidden server requirement of five profession types online simultaneously.
- Fair participation credit, cooperative progress announcements, local/world announcements and privacy choices; anti-griefing rules for shared resource use and major world decisions.
- Production-safe analytics and balancing views: time to stage completion at populations 1/2/5/10/30, per-vocation activity participation, stalls, abandoned projects, regional threat suppression, and exploit patterns.
- Performance design: project updates are authoritative events and compact replicated snapshots/deltas, not network replication of thousands of individually editable tiles. Tilemap overlays/interactive Actor replacements remain deterministic, stable and reconnection-safe.

### 5.3 Solo-to-30 progression formula policy

Document and implement an **explicit population-sensitive contribution model**; do not simply multiply every health bar and resource quota by concurrent player count. Use stable, auditable windows such as active engaged participants over a recent bounded period, not momentary logins that instantly change a project deadline. Separate **essential milestones** completable by one person from **optional group enhancements**. Avoid sudden thresholds, oscillating goals and exploits where logging additional accounts lowers work. Each objective has an absolute solo-completable route and a visible estimate of remaining personal effort. A player should never lose credited progress when another logs in.

At the design stage propose a starting algorithm, write its assumptions and counterexamples, test with simulated populations and actual multi-client fixtures, and only then treat it as the recommended tuning. Do not manufacture measured timings. The intended qualitative contract is: **comparable personal time-to-value and full content access**, not mathematically identical world completion speed or equivalent social experience at every population.

## 6. Persistent online architecture and supplied multiplayer plugin

### 6.1 Inspect the exact supplied plugin first

The attached ZIP contains `Plugins/MultiplayerSessions/` (`VersionName 1.0`, author attribution Stephen Ulibarri), with a C++ `UMultiplayerSessionsSubsystem`, C++ `UMenu`, `.uplugin`, `MultiplayerSessions.Build.cs`, and a demo `WBP_Menu.uasset`. It uses the legacy Online Subsystem session interface and declares OnlineSubsystemSteam dependencies. The menu defaults to listen-hosting, not headless MMO zone hosting. These are **verified from archive source files**, not compilation proof.

Before using the plugin, create a **line-referenced plugin compatibility/gap table** from actual source and explain these specific issues:

- The provided plugin offers session create/find/join/destroy delegation and basic host/join UI, not a standalone account service, persistence store, regional state service, match/zone allocator, world-project ledger or cross-server transfer orchestration.
- `StartSession` and `OnStartSessionComplete` are empty; do not claim implemented session lifecycle. Audit for missing or unused end-session/update support.
- `CreateSession` calls asynchronous `DestroySession` for an existing session but does not return before continuing immediate creation; document the race, intended state-machine/sequence fix and regression checks instead of copying it blindly.
- Menu construction uses a `?listen` lobby URL, and the default path references a sample third-person lobby path (`/Game/ThirdPersonCPP/Maps/Lobby`). Replace examples with new authored 2D maps and distinguish **listen-server testing** from a production dedicated world server.
- Menu `OnJoinSession` does not gate travel on a successful join result and resolved valid address; the no-match session-search case can leave the Join control disabled. Track UI recovery and error-state cases explicitly.
- Session operations dereference a local player/unique network ID without a safe dedicated-server/no-local-player path; determine required server-specific creation/advertisement responsibilities separately.
- Steam is enabled/linked as a plugin dependency; document a local LAN/Null-subsystem test path and a separately verified Steam option, including platform/test-account constraints and dedicated-server-specific configuration. Do not confuse the old Online Subsystem and newer Online Services APIs as interchangeable.
- Correct delegate lifetimes, repeated MenuSetup binding/unbinding, null checks, duplicate requests, destroy/host retry, session filtering, testing with two external processes, and actual source/API compatibility with the installed UE 5.8.3 and selected provider. The plugin has source and one `.uasset`; no test results or explicit reusable distribution license were established from the ZIP.

**Decide and document whether to adapt the plugin through a small, verified session/connection adapter or replace it for dedicated servers.** The default recommendation is to **retain it as an instructional prototype and possible local session bootstrap**, then expose a narrow `Connection/Session` abstraction for the real game's login/realm selection. Do not silently throw it away, but **do not build server persistence or character authority on it**. No duplicate overlapping online session managers. Do not modify/distribute the input plugin ZIP unless explicitly authorized. Keep a compatibility decision record: Used as-is / Adapted after checks / Replaced, with evidence, tradeoffs and fallback.

### 6.2 Actual game authority boundaries

Define a small, plausible production baseline with independently understandable responsibilities:

- **Client:** input and permitted prediction, menu/character creator, 2D presentation, local configuration, UI, camera, sound, cosmetic animation, preview. Client does not own currency, world stages or items.
- **Unreal dedicated zone server:** validates movement/abilities, AI decisions, enemy encounters, local harvest/fishing/crafting action permission, nearby state replication, region actor projections, interaction distance, party-local events. Each client connects to one authoritative gameplay server at a time.
- **Durable server-side persistence boundary:** owns canonical character identity/appearance/vocation/combat skills, inventory/equipment/currency, quests, profession mastery, project contributions, realm regional stages, receipts and versioning. It can begin as a small, controlled persistence service/store, not a premature mesh of microservices.
- **Session/realm directory and transfer coordinator:** maps player/account/character identity to current realm and zone, authenticates transitions, enforces character-session leases, capacity rules, reconnect routing, zone assignment and timeouts.
- **Shared social/economy service only where genuinely needed:** trade ledger, party/guild membership and chat routing may use existing boundaries or minimal services; avoid premature service proliferation and duplicated player records.

For each meaningful mutable fact, name **one authoritative writer**, **storage location**, **replication projection**, **lifetime**, **client command route**, **revision or idempotency key**, and **recovery/rollback behavior**. Explicitly compare `GameMode`, `GameState`, `PlayerController`, `PlayerState`, `Pawn/Character`, `GameInstance`, server-only service and database record. Never call an Unreal Actor pointer a persistent cross-server identifier. Clearly distinguish owner from viewer; replicate views appropriate to privacy.

### 6.3 Region/biome travel and realm lifecycle

- The fantasy world consists of substantial authored 2D biome maps connected by real transitions/roads/gates/boats, with loading screens. The world is **not** one endless TileMap; build streaming/instance policies only when profiling indicates need.
- Document **single-zone-server map travel** versus **independent server-to-server character migration**; changing a whole server map would displace every connected player, so is not the default MMO zone-crossing behavior.
- Zone transfer protocol: stop new gameplay commands → mark source session as transferring → snapshot verified character state and position/requirements → securely reserve destination and issue short-lived single-use transfer token → commit/fence authoritative ownership → load destination client with progress UI → validate destination/start location and consume token → activate new possession and subscriptions → complete/retire source → recover on timeout, disconnect, repeated token or failed destination.
- Clearly differentiate authoritative transfer state from cosmetic loading screens and from a normal player death. A previous body cannot accept transactions once its session lease expires.
- Have an **authoritative world clock** per realm (or explicitly coherent regional clocks), server-owned day/night/weather transitions, map overlays and gameplay modifiers where implemented. Weather affects existing authored mechanics without generating impossible client/server disagreements.
- Account creation/auth, secure character selection and new-character validation: creator-chosen unique display name, bounded name policy, allowed body/palette/hair/outfit from actual asset catalog, **required vocation selection**, character-slot limits, starting inventory/zone, server-side creation transaction, safe delete/recovery, reconnect and duplicate-login prevention. Treat identity provider choice and security/privacy requirements as decisions to verify, not a built-in feature of the supplied ZIP.

### 6.4 Critical concurrency and exploit rules

- Server-side compare/commit or database transactions for material debits, item creation, currency, mail/bank, equipment swaps, buy/sell, direct trade, fish catches, quest rewards and world contributions. No client-generated authoritative Item GUIDs, completed quest flags or reward rolls.
- Distinguish **item definition IDs** from **owned item instance IDs**, **resource site IDs**, **cast/action IDs**, **zone IDs**, **character IDs**, **world project IDs** and **transaction receipt IDs**. Preserve auditability across zones/restarts.
- Replay, rapid-click, simultaneous clients, stale cached data, late RPC, interrupted animation, failed save, database rollback, zone crash, session takeover and reconnect must never duplicate or lose a committed outcome without an explicit detection/recovery path.
- Include privacy, authentication/session-token hygiene, command validation, network relevance/interest management, rate limits, suspicious behavior diagnostics, moderation, account bans, admin audit, logs and backup/restore. Do not invent anti-cheat as a single magic checkbox.
- Performance targets must come from actual profiling with 1, 2, 5, 10 and 30 concurrent connected clients, plus cases where many players interact with the same node, NPC, project or encounter. State environment, network conditions, profiling procedure, budgets and whether the results were actually measured.

## 7. Required individual gameplay system chapters

**Do not write a feature checklist without implementation guidance.** For every item below, the new guide must contain a complete beginner-friendly system chapter (or a clearly linked subsection in a dedicated chapter) including the player-facing mechanic, authorable definitions, C++ authority, Blueprint exposure and Editor settings, exact folder and consumer wiring, UI, animation, persistence/replication, validation/failure policies, and a repeatable solo plus multiplayer test. Every chapter must distinguish future balance examples from hard engine requirements.

### 7.1 Character/account/frontend

- Login/realm select, character-slot management, character select, mandatory primary vocation choice, optional independent combat discipline, supported body/hair/palette/outfit previews, readable error states, starting kit and tutorial, naming and uniqueness, confirm/rename/delete policies, account recovery, reconnect, logout, duplicate login, permissions and privacy.
- Character presentation from actual compatible sprite layers with hair/hat/cloak/tool/outfit choices, base/outfit page fallback, paper-doll visual ordering and remote avatar sync; cap NPC appearance customization at authored combinations until assets exist.
- Player sheet showing combat level, chosen vocation/mastery, skills, stats, tools, achievements, quest history, region contributions, persistent progression and active temporary state. State exactly what is public (nameplates/appearance) and private (inventory/account details).
- Profession creator must not masquerade as class selection: communicate both progression axes and prevent story/gear dead ends. Unsupported vocation-specific art never invalidates a valid character record.

### 7.2 2D movement, controls and collision

- Eight-way directional input on a flat gameplay plane with **four-direction sprite rendering first**, consistent normalization and facing priority; camera fixed with zoom only; character movement acceleration/braking, sprint, dodge/cooldown/stamina, short server-validated jump/hop over authored low obstacles, water enter/exit and swimming, obstacle collision; **no climbing and no precision platformer traversal**. Where hop/swim art is missing, use safe labeled temporary visuals and track required sprite work.
- Paper2D tile colliders, hazards, doors, interactable objects, map chunk/tile loading, depth/occlusion, Y-sort, one-way visual layering for trees/roofs, editor debugging and AI path coverage. State how engine collision/nav data is set up for a 2D map without inventing an automatically working navmesh.
- Native/Enhanced Input actions for movement, primary/secondary attack, ability bar, item/use, interact, roll, sprint, target cycling, inventory, professions/journal/map, fishing phases, menu confirm/cancel/chat; UMG focus and control remapping. Multiplayer UIs cannot pause authoritative world time.
- Network input permission, interpolation/prediction when needed, incorrect-position correction, spoofed movement rejection and packet-loss tests, plus remote directional animation and equip visibility.

### 7.3 Combat, class roles and enemies

- Hybrid: responsive action hitboxes/traces for melee and projectiles, optional soft-target selection for abilities/heals, smart target fallback, enemy line of sight/range, mouse and controller support; authoritative hit/accuracy rules, damage events, dodge/guard/block, stamina/mana/health, armor/resistance, critical hits, ability costs, timers, casts/channel interrupts, healing/utility effects, status conditions and group credit.
- **Prefer Gameplay Ability System (GAS) as a documented design choice** for attributes/abilities/effects/cooldowns if proven compatible with the targeted engine/project. Show actual GAS role boundaries vs custom data/AI/PaperZD presentation. Avoid re-implementing a parallel attribute/cooldown framework and avoid assuming GAS handles persistence, gameplay quests or MMO matchmaking.
- Four proposed combat disciplines (Vanguard, Ranger, Arcanist, Warden), class/discipline-specific skills and talents, level-up XP tables, attribute derivation, mutually exclusive specialization branches, respec and clear safeguards against mandatory-progress lockout. Allow ranged/healer characters to progress solo using appropriate abilities or NPC help; no class requires a full human party.
- Data-driven enemy families, patrol/roam, aggro, perception, threat, leash, evade, spawn/respawn, regional threat participation, melee/ranged/elite/boss patterns, projectile and AoE collision, interrupt/telegraph, server-owned legitimate death and reward credit, support/healing credit, group XP and loot, anti-kill-steal and no duplicate corpse rewards.
- Boss fights/dungeons have multiple **authored mechanics variants** for one human vs groups; do not solve scaling by multiplying hitpoints. NPC allied characters may substitute for missing role mechanics when validated. Document target budget, NPC AI limitations, boss reset and wipe policy, accessible alternative solo pathways where a 30-player combat space would otherwise be impossible.
- Death/graveyard/recovery: server-side checkpoint selection, clean restoration, safe temporary effect reset, persistent gear/quests retained, reasonable durability/currency penalties if chosen, no losing world-project progress. Server disconnect during combat must have a defined fair policy.

### 7.4 Items, equipment, loot and progression

- Authored item catalogs vs owned instances; stable IDs, stack sizes, bags, bank, capacity, tools, consumables, durability and repair, bind/trade rules, rarity Common→Legendary, controlled affix generation, item level/prerequisites, descriptive tooltips, stat/equip effect rebuild and content-version migrations.
- Gameplay equipment slots: Head, Chest (`Top` equivalent), Legs (`Pants` equivalent), Hands, Feet, Waist, Shoulders, Cloak, Main Hand, Off Hand, Necklace, two Rings and two Trinkets. Logical equipment and crafting support must not promise sprites for each; fallback may be a complete outfit layer plus separate headwear/cloak/tool where the archive supports it. One- vs two-hand conflicts, shields, visual skin overrides, gear comparison and server validation.
- Creature loot tables: weighted/guaranteed drops, individual/shared loot rights, party/group options, coins, monster-specific materials, random affix limits, inspectable roll algorithms and drop-rate testing, equipment and inventory full errors, death/reload anti-replay receipts.
- Combat XP, quest XP, vocation XP and regional contribution reputation are separate ledgers/tables. Combat level proposals and XP caps must remain authored tuning; do not grant level-up points again on import or force crafting players to grind combat XP to pursue basic professions.
- Equipment/audio/UI synchronization after character login, region transition, recovery, respec and replicated remote appearance; no inventory or stat calculation inside a widget.

### 7.5 World-gathering system: mining, woodcutting, herbalism and salvage

- **Server-selected randomized resource spawns** at authored biome-eligible sites, not arbitrary world coordinates. Include candidate locations/tags, proximity/spacing, walkable collision, blocked doors, resource grades, time/day/weather modifiers if approved, cap on active sites, seeded/auditable selection, depletion/regen, expected density and progression balance.
- All characters may gather basic resources; vocational mastery alters methods, decision options, quality control and advanced materials. Forgekeepers are not just miners; Woodwrights are not just log cutters. Salvage expeditions and forestry protection can complement standard nodes.
- A gathering command has a server-valid site ID, permitted action/tool/range, timed action with cancel policy, contention/exclusive claim or per-player quota policy, one durable item grant and mastery reward, depletion state and replicated visible node. Write a two-player same-node race test, reconnect-before-respawn test and 30-player hotspot test.
- Protect against resource-hoarding, spawn camping and overpopulation while keeping regional economies useful. A solo player must have enough material acquisition paths without waiting for server neighbors to clear contested nodes.

### 7.6 Fishing and aquatic systems

- Use available Mana Seed fishing `p3` poses and rod layer, plus verified water/environment assets if supplied later. Describe water eligibility, fish spawn/species tables by biome, season/time/weather changes, cast direction/aim, bobber overlay/sprite, wait and bite cues, reaction/reel decision, equipment/bait, catches, failure and accessible interaction timing.
- Server validates every cast and catch; no client timer/animation grants fish. One catch per cast ID, no stale bites after movement/combat/zone departure/death, server-awarded vocation XP and item, cancellation and rollback/recovery rules.
- Integrate catches into cooking/baking, alchemy, NPC deliveries, regional festivals, ecology discoveries, rare collections and meaningful markets. Fishing is a gameplay branch, **not** a required five-minute idling action before every craft.

### 7.7 Farming, food, baking and the Hearthkeeper loop

- Document personal or leased farm plots (define ownership to avoid grief), seeds, watering/soil, growth states, harvesting, produce quality/tuning, season/weather modifiers and server-side progression that does not penalize real-life absence. Shared town gardens are optional and permissioned.
- Ingredients from fishing/farming/foraging → authored recipes → cooking/baking decisions → food buffs/healing/expedition supply → merchant and world-project consumption. Define station interactions (oven/campfire/mill), recipe unlocks, item creation, food safety/status effects, expiration if any and inventory storage.
- A Hearthkeeper can complete an expedition to find a special ingredient, defend their food supply, and make tactical menu decisions. Test full recipe with a single player and then two interacting characters, one of whom has another vocation.

### 7.8 Forging, carpentry, alchemy and general crafting

- Shared recipe definitions, recipe prerequisites/mastery, tools, crafting stations, stack-accurate material validation, optional currency/service charges, item properties, deterministic initial outcomes, controlled advanced quality/affix outcomes, station availability, interrupt policy, secure server transaction, craft receipts and advancement. No speculative player crafting arbitrary custom code or a complex programmable crafting engine.
- Blacksmithing links mining, salvage, alloys, weapons, repairs, caravan protection and settlement upgrades; carpentry links timber grades, bows, furniture, traps, bridges and forest repair; alchemy links plant discovery, field research, antidotes, potions and regional illness; cooking links agriculture, fishing and travel preparation.
- Explain partial stack use, equipment instance IDs, inventory full, missing station, character disconnect immediately after commit, rolling content updates, currency/item rollback, rapid double-click, simultaneous crafting requests, and zone restart. If craft time is used, specify when ingredients are reserved versus consumed and what happens on cancellation.
- Balance player-crafter relevance without forcing player transactions: NPC basic services/commission boards remain available when only one player is online; player specialists should offer flexibility, variants and identity, not monopoly over essential gear.

### 7.9 Questing, NPC services, dialogue and factions

- Data-driven quests with kill, gather, fish, plant/harvest, craft, deliver, talk, interact, research, scout/map, dungeon, rescue, defense and regional project contribution objectives. Journal, notifications, quest chains, repeatable regional contracts, prerequisites, quest sharing with eligibility checks and distinct personal vs global completion.
- Branching, state-sensitive NPC conversations, reusable dialogue conditions, choice effects with persistent flags, localization-ready text, cancel/travel cleanup, and reactions to danger/development/discovery. State whether a conversation pauses local input; it must **not pause the multiplayer world**.
- Merchant, trainer, quest giver, vocational mentor, guard, town official, bank, crafting station and faction representative roles; an NPC can offer several services through explicit service definitions without inheriting conflicting actor parents or mutating inventory directly.
- Original faction/reputation system with bounded updates and authored benefits; user-friendly alternative quest routes that cannot be permanently blocked by selecting a vocation/combat discipline.
- Time/day/weather and schedules affecting fishing, creature activity, NPC presentation, crop conditions and certain quests. Avoid permanently inaccessible story objectives due to real-life clock windows; offer predictable alternate schedules/windows.

### 7.10 Economy, NPC merchants, banks and player trade

- Currency stored authoritatively as a smallest-denomination integer; optional display as copper/silver/gold only. Server-mediated buy/sell/buyback/repair, stock/restock, discounts, restrictions, audit receipts, bank deposits/withdrawals, sell safeguards and lossless full-inventory rejection.
- Player-to-player trading with two-sided explicit confirmation, revisable offers, exact item instance IDs, server escrow/atomic commit, currency, disconnection and duplicate-confirm recovery, safe UI and anti-scam rules. Player storefronts/auction house are future extensions requiring separate evidence and trade security review.
- NPC baseline prices/stocks must let a solo player obtain critical supplies and complete necessary production chains. Do not let empty player markets block advancement. Human trade can offer better choice, specialization and social interaction.
- Regional commerce: caravans, supply routes and new merchants unlock through projects and danger reduction. Caravans can create escort/defense challenges without forcing repeated cross-map delivery chores.

### 7.11 Exploration, cartography, secrets and long-term world content

- World map and minimap, fog of war/personal discoveries, map notes, waypoint markers, safe route tracking, hidden trails, secret rooms, ruins, environmental clues, collectibles, profession-specific discovery bonuses, per-realm shared discoveries and clear policies for uniqueness.
- Wayfinder combat-adventure gameplay must include tracking, finding creature lairs, solving authored route clues, scouting camps, sharing optional maps and leading expeditions, not only filling a progress meter by stepping on map coordinates.
- Design **at least six connected original biome-region families** (e.g., sheltered valley, ancient forest, flooded marsh, rocky highlands, deep mountain, storm coast) with a hub village, logically accessible loading transitions, multiple quest/resource loops, landmarks and services, threats, construction projects, fishing/forest/mine interactions and a consistent sense of geography. These are authored design targets, not claims of existing maps.
- Supply a production pipeline for expanding one biome via data-driven registries, 2D tile atlas, decoration/occlusion layers, player/AI collisions, eligible gathering sites, fishing waters, quest/NPC definitions, world states, multiplayer replication, danger tuning, map/minimap, performance, return travel and automated content verification. New content should not require writing new C++ for ordinary items or NPCs.
- Exploration remains rewarding for established players through authored repeatable routes, new regional threat stories, rotating discoveries and profession activities. Do not resort to an infinite procedural quest promise or invalidate the history of permanent town improvements.

### 7.12 Social play and groups

- Persistent online-presence rules, proximity/local/global/party/guild chat with privacy and moderation, friends/block, party invitations and role selection, quest sharing, group loot, support credit, player trading, guild identity/ranks/permissions and shared regional contribution boards.
- Co-op caravans, joint crafting/supply expeditions, exploration maps and dungeon challenges should allow solo action without requiring parties. Real group play can make strategic interactions richer, not be the only path.
- Distinguish 1–30 simultaneous population on a zone/realm test server from max dungeon group size. Define tuning and tests for solo, duo, small party and busy region. Group-only social actions naturally need other humans, but **no mandatory main story, essential crafting tier, profession mastery or critical region upgrade requires those interactions**.
- Prevent griefing of crops, tree stands, project contributions, trade and rare monsters; privacy/proximity limits and permission checks on shared buildings. PvP, conquest, taxation, political elections, player housing and massive open-world raids are **deferred optional extensions**, not required for the committed version.

### 7.13 Audio, visuals, UX, accessibility and live operations

- Stylized 2D animation/audio/VFX feedback for attacks, blocks, crafting, gather, fish, environment time and weather, world constructions and UI. Clearly state visual feedback is not the source of gameplay authority.
- All screens: login, character creation/vocation comparison, character selection, HUD/hotbar, map/minimap, combat target/party bars, equipment/paper-doll preview, bags/bank, vendors, loot, quests/journal, professions/crafting/recipes, fishing, farm plots, contribution board, region threat display, dialogue, social/trading, chat/guild, settings and errors/recovery. Show information hierarchy, focus rules, controller selection, UI-only vs gameplay input, screen-reader/text alternatives where applicable, readable pixel fonts and scalable UI.
- Network quality indicators and explicit errors for full zone, transfer failed, stale inventory, disabled service, no eligible fish, skill restrictions, pending save, not authorized, maintenance, trade timeout, plugin unavailable and disconnection.
- Localization-ready quest/dialogue text, color-blind-safe UI cues, controller/keyboard rebinding, text scaling, reduced motion and forgiving timing alternatives for fishing/crafting challenges. Sound cues must have equivalent visual information.
- Dedicated-server deployment, config/secrets, environment selection, backup/restore, schema migrations, content version alignment, telemetry, moderation, support tooling, data lifecycle/privacy, metrics, profiling, packet loss, soak tests, crash and partial database failure.

## 8. Mandatory end-to-end system interaction examples

Do not merely list these as 'ideas'. In the finished documentation, write **complete worked walkthroughs** with sequence diagrams, data IDs, asset names, owner boundaries, C++/Blueprint responsibility, UMG user journey, exact test fixture setup, expected successful outcome, duplicate/rejection behavior and server restart/disconnect result:

1. **New character and vocation:** create a character, choose Hearthkeeper, preview supported appearance, pass server validation, persist chosen vocation and enter starter village. Reconnect/rejoin through another client and show identical appearance/vocation and no duplicate profile.
2. **Solo Forgekeeper loop:** prospect a rare vein, defeat an enemy while retrieving salvage, mine/harvest, craft a weapon fitting, repair a watchtower, advance vocation and settlement stage. The solo player uses no human service and receives one correct contribution credit.
3. **Solo Hearthkeeper loop:** cast/fish at a server-valid pool, plant or harvest ingredients, bake a provision, help a caravan and advance a settlement objective; interrupted fishing and full inventory do not grant extra fish.
4. **Solo Wayfinder loop:** examine tracks, map a hidden route, overcome a skirmish, reveal an authored threat, report it to an NPC and unlock a shortcut. Discoveries are correctly personal/shared; reentering the region does not replay a reward.
5. **Woodwright + Apothecary loops:** harvest sustainable timber, craft defensive supports, defend and repair a road; discover rare medicinal reagents, craft a remedy and resolve a regional condition. Both can be completed solo with normal gear.
6. **Randomized 2D resource nodes:** server picks eligible forest/mine tile sites; two players attempt the same exclusive vein/tree; at most the allowed claim succeeds, every accepted harvest receives one receipt and resource respawn survives map unload. A 30-player crowded region remains fair without unusable permanent depletion.
7. **Combat and loot:** one player fights an enemy, another joins, both obtain appropriate XP/credit/loot under a declared rule. Hitbox, ability cost, target and loot are server-owned; exploit/replay/kill-steal cases produce no duplicates.
8. **Recipe race:** craft an armor item while two requests arrive, disconnect after confirmation and rejoin. Materials and currency debit once, the equipment instance exists once, vocational progress is correct, and worn art uses only supported sprite layers.
9. **NPC merchant and self-sufficiency:** solo Wayfinder buys a basic repair item from NPC, earns money from quests, sells a surplus, commissions another-vocation item, and finishes story without a human crafter online. Confirm trade cannot create negative funds or bypass profession requirements.
10. **Living Region construction:** five distinct vocation contributions lead to road repair and visible tile stage; one player can satisfy equivalent essential stage via alternative NPC-approved objectives. A second player joins at 70% completion and sees accurate progress without tile actors granting rewards on load.
11. **Regional threat and legendary hunt:** track clues, reduce camp threat, defeat an authored regional leader and see changed patrol locations/merchant route. Test one-human difficulty variant with helper NPC and group variant with several real humans.
12. **Single-player dungeon vs group dungeon:** enter an encounter alone with permitted NPC aid and achieve the same critical narrative/world milestone; run with 2/5 players and show more collaboration but no monopoly on essential rewards. Solo AI cannot farm rewards while player idle.
13. **Biomes and world persistence:** one player crosses loading boundary to a distinct authoritative zone, while a second stays. Both maintain correct avatar/inventory and region stage. Transfer expiry/duplicate token/target server loss does not duplicate character or items.
14. **Busy server:** connect 30 clients in a region with parties, chat, harvest, construction, enemies, vendors and zone boundary activity. Benchmark resource contention, UI state, replication and backend command counts; compare to a one-player reference run, do not claim unmeasured capacity.
15. **Isolation of UI from rules:** remove HUD, close crafting/menu widgets, destroy/reopen merchant panel, recreate character on new map, and repeat the same authoritative commands. No widget is the only location that applies a skill, completes a quest, records region state or enforces stock.

For *each* example include at least one valid path, rejected command path, concurrent path, reconnection path, and `not yet implemented` stage where the system is deferred.

## 9. Detailed incremental development roadmap — 32 small phases

Maintain the original guide's spirit: **a phase is finished only when the feature is wired into the actual player/game state, configured in a real development world, and an explicit acceptance test passes.** The future manual may adjust exact ordering if its checked dependency graph exposes a hard incompatibility; document and update every dependent index rather than changing the list silently. All 32 phases are **planned documentation requirements**, not evidence any code has been executed.

| Phase  | Build target / bounded output                                                                                                        | Mandatory integrated proof                                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **00** | Source/asset/plugin audit, Unreal engine evidence, rights, development environment, authoritative registries and C++/Blueprint rules | Document all known/unverified dependencies; develop an actual import/build verification checklist and no false pass claims                |
| **01** | Four-direction Mana Seed character preview, layered sprite import, directional PaperZD test and paper-doll compatibility             | One character with hair/hat/outfit/tool renders all supported poses; art gaps reported rather than hidden                                 |
| **02** | 2D top-down tiles, collisions, occlusion, scene sorting, fixed zoom camera and starter village map                                   | Move around trees/roofs/water without collision or sorting failures; no 3D landscape appears                                              |
| **03** | Eight-way control input and four-facing presentation, sprint/dodge/interact, damage-independent animation states, controller input   | Keyboard/controller reach all walkable tile paths; diagonal speed, hop collision, water transitions and dodge interruption are consistent |
| **04** | Supplied sessions-plugin bridge decision, host/join prototype and actual dedicated server with two separate clients                  | Two clients see a server-owned avatar and cannot modify authoritative location/state; plugin gaps remain visible                          |
| **05** | Login/character creation/selection, required vocation choice, appearance/layer preview, introductory combat-style setup              | Create Forgekeeper/Hearthkeeper/Wayfinder prototype record; invalid/duplicate choice and names rejected                                   |
| **06** | Durable character/realm models, ID and transaction ledger, schema versions, reconnect and server restart                             | Solo character and second client preserve identical canonical progression without duplication                                             |
| **07** | Two connected 2D biomes with loading screen, persistent identifiers and per-player zone migration                                    | One character transfers while another stays; retries/failures preserve one authoritative character                                        |
| **08** | Interaction routing and safe action arbitration: NPC, item, gather, object, water; UMG requests/observes                             | Client cannot activate an out-of-range/busy/expired interaction; one player can interact end-to-end                                       |
| **09** | Hybrid melee/ranged combat, resources, target validation, cooldown/cast, GAS/animation integration                                   | Solo and two-client player attacks affect server-owned dummy once; latency/missing-notify regressions                                     |
| **10** | Enemy AI, aggro/leash, death/respawn, kill rewards and combat XP                                                                     | Solo and two-client battle with real enemy grants XP once; no reward replay after restart                                                 |
| **11** | Item definitions, bags, equipment, paper-doll rendering, random weighted loot and consumables                                        | Loot, equip/unequip, appearance, stat rebuild and reconnect work with no duplicate item instances                                         |
| **12** | Combat disciplines and talents, vocation model/mastery and initial vocation UI/skill trees                                           | Valid skill purchase persists; class and vocation XP remain separate; dead-end prerequisite rejected                                      |
| **13** | NPC dialogue, quest objectives/journal, starter quest chain, vocation mentor contracts                                               | Character completes one multi-step quest alone; joining mid-quest never double-grants reward                                              |
| **14** | Eligible randomized ore/tree/plant/salvage sites, server harvest and respawn                                                         | Solo gather progresses; two clients cannot both claim exclusive site; dense-region spawn remains walkable                                 |
| **15** | Forgekeeper complete mini-loop: prospect, recover salvage, smelt/forge, repair, defend                                               | Solo plays Forgekeeper outing plus one world-project material, gear usable and restart-safe                                               |
| **16** | Fishing water/pools, bite/catch/cancel, species tables and actual p3 sprite states                                                   | Solo catches fish exactly once per cast and animation/zone reset never duplicates catch                                                   |
| **17** | Personal farming plots, planting/growth/harvest, ingredient production and cooked/baked food                                         | Solo plants, fishes, bakes an expedition food item; no offline crop deletion or rival harvesting exploit                                  |
| **18** | Hearthkeeper full mini-loop, food provisioning contracts and variation                                                               | Solo reaches vocation advancement by mixing water/field/kitchen and an expedition objective                                               |
| **19** | Wayfinder exploration/cartography, tracks, hidden routes and skirmish encounters                                                     | Solo scout discovers route and threat, fights, reports it, gains personal/shared discovery once                                           |
| **20** | Woodwright timber management, carpentry, replanting, defense assets and quests                                                       | Solo sources eligible timber, crafts a bridge support and restores an authored forest/road state                                          |
| **21** | Apothecary herb discovery, field research, alchemy and support/curative quests                                                       | Solo collects safe reagents, solves regional illness challenge and crafts a useful antidote                                               |
| **22** | Living Regions schema: durable development/danger/discovery records, snapshot/delta presentation, UI boards                          | Solo and a newly joined second client see the same staged region state after restart                                                      |
| **23** | Shared construction objectives, alternative solo contribution routes, NPC visual/service/world transitions                           | Solo repairs a bridge through available methods; 2/5/10/30 cannot duplicate contributions                                                 |
| **24** | Region danger, enemy camp escalation, clue-driven legendary hunts, patrol and NPC reaction events                                    | One human can resolve essential threat; group roles add tactical variety; danger resets by authored policy                                |
| **25** | NPC merchants, currency, buy/sell/repair/bank, trade escrow, player-vocation market relevance                                        | Solo provisions without player trade; two clients trade securely; stale balances and retries fail cleanly                                 |
| **26** | Deep solo-to-30 balance, scalable encounters/projects, hireling NPCs and world-content parity                                        | Automated/controlled tests at 1,2,5,10,30; core PvE never requires a human group and scaling avoids goal oscillation                      |
| **27** | Party/group XP and loot, chat/friends/block, guild contributions, social boards and permissions                                      | Solo remains fully playable; a group can coordinate without griefing or duplicating credit                                                |
| **28** | Dungeons, regional bosses, cooperative expeditions, companion substitution and instance recovery                                     | Same critical milestone obtainable with one human and with parties; boss variants validated                                               |
| **29** | Six-biome authored content factory, end-to-end original quest arcs, fast travel/route coherence, weather/day-night                   | New biome with authored tiles, content IDs, spawn rules, map, loading return path and solo route added without code rewrite               |
| **30** | Full UI/UX and accessibility, controller navigation, audio/VFX, localization, content balance and quality-of-life                    | All real game features reachable from screens that do not own rules; screen-independent regression passes                                 |
| **31** | Security/ops/anti-cheat, deployment, performance/packet-loss, package proof, backup/recovery, content migrations and doc audits      | Truthful packaged server/client validation at populations 1/2/5/10/30 (where environment permits), failures named explicitly              |

**Do not** place all classes and assets in Phase 00; make each phase's creation order dependency-aware, generating one minimal feature slice at a time. No phase ends at 'created class shells': every relevant asset is assigned, consumed, instantiated in a test map, exercised and regressed against prior systems.

### 9.1 Mandatory format for each phase's own HTML page

Each `phases/phase-XX.html` must supply these fully authored sections:

1. **Player-visible outcome and why this phase is next.** State the precise value it adds to each pillar and whether a solo player can access it today.
2. **Prerequisites and hard blockers.** Exact previous phase tests, required engine/plugins/art imports, checked expected versions, and validation needed to avoid building on unsupported integration.
3. **Create now / do not create yet.** Machine-generated asset creation table with exact name, Unreal type, native parent or interface, actual `Content/Game/...` and `Source/RPG/...` paths, relevant Data Asset schema/instance distinction and availability of sprite frames.
4. **Editor/configuration steps:** where to navigate/click, asset parent selection, required settings/components, 2D collision/sorting, Input Mapping, PaperZD or GAS setup, server/project configuration, expected data table fields, and how to verify each initial configuration. Do not invent default native Blueprint nodes or pretend custom functions are preinstalled.
5. **Native ownership contract:** exact C++ role, method/field/API declaration shapes in prose or clearly marked pseudocode, runtime state ownership, Blueprint exposure and restrictions. Do not write actual game source files.
6. **Reopen existing consumers:** exact previously authored player/NPC/world/server/model/widgets to modify; what reference or event/contract to assign; expected initialization and teardown order; listener bind/then-pull rules; failures when referenced definitions are missing.
7. **Develop a test map/service fixture:** named map, NPC, enemy, resource node, fish pool, profession recipe, UI screen, test realm/account and seeded datastore state, with exact settings and sample values clearly labeled as test fixtures.
8. **Run now:** exact human editor/packaged steps. At minimum describe one-human server test for every PvE phase, two-client test for shared state and a documented 30-client load case for relevant concurrency features.
9. **Success/rejection/regression:** state observable values, expected persistent records, anticipated errors, idempotency/latency checks, visual checks, prior-phase loops to rerun and what a new engineer should inspect when it fails.
10. **Scope boundary and maturity:** development-only placeholders, art holes, features deliberately staged/deferred, compiled vs documentation-only verification and explicit stop condition.

Use an original **small but complete starter route** as the repeated integration test, not 32 separate unconnected sandbox rooms. A phase is complete only if its feature can be exercised from the actual player flow in a configured map, not only from debug buttons.

### 9.2 Four vertical slices with acceptance evidence

**Slice A — authoritative 2D adventure (after Phase 10).** One human and two remote clients can create/choose a starting character, move through a 2D village/wilderness, cross two connected biome zones via a loading transition without displacing other players, attack a server-owned monster, receive XP, reconnect and recover. Sprite facing/layering survives remote observation. Document every source-of-truth transaction and plugin limitation. No gameplay `.uasset` should be described as generated by documentation.

**Slice B — the first vocation adventure (after Phase 18).** Play separately as Forgekeeper, Hearthkeeper and Wayfinder through authored starter quests and mixed actions: combat, mine/log/salvage, fish, farm, cook/bake, forge and map a route. Include a merchant, weighted loot, equipment and one starter contribution board. All three available prototype paths are achievable with one connected human; two connected humans may collaborate.

**Slice C — Living Regions and full vocation roster (after Phase 26).** Five vocations have actual playable loops; one solitary player can complete a meaningful bridge/watchtower project and local danger event. New clients see the world state; five/ten/thirty clients create more interactions but cannot lock solo access. Every vocation contributes differently; resource sites remain fair and server restarts preserve completed stages. Validate 1/2/5/10/30 where actual runnable test infrastructure exists; report gaps honestly.

**Slice D — online-ready content and safety (after Phase 31).** Players can experience original biome arcs, party or solo dungeons, secure trade, guild/social flow, region threats, all major UI, full character/vocation systems and deployed test services. Run packaging, crash/reconnect/restart/backup, bad-data, exploit/replay, profile performance and document what was proven. Do not claim a globally scaled MMO or live operations without actual deployed evidence.

## 10. Per-asset technical reference and one authoritative registry

Create a single machine-readable `sources/current-asset-manifest.json` declaring **every game-facing asset** needed for the committed game, including planned C++ class/module, Blueprint class/child, native Component/interface, Data Asset schema/instance, Structures/Enums/Gameplay Tags, Data Table, Paper2D sprite/flipbook/TileSet/TileMap, PaperZD source/sequence/AnimBP, UI widget, Input Action/Mapping Context, map/level, effect/VFX/audio definition, NPC/resource/quest/profession recipe/region definition, test fixture, network/back-end contract, database record, and source-art compatibility reference. Use concrete canonical names and preserve them after declaration. Do not pad the register with unused classes or generic redundant managers.

At minimum each registered asset has: `name`, `type`, `parent/native_base`, `exact_game_path_or_source_path`, `first_phase`, `first_active_phase`, `owner`, `lifetime`, `replication`, `persistence`, `status` (`design/fixture/art-present/blocked/verified`), `dependencies`, `reverse_users`, `description`, `doc_path`, and a clear split between **engine-built**, **custom C++ future work**, **Blueprint authoring**, **imported art**, **backend contract**, and **offline documentation**.

Each asset gets its own linked technical page covering:

1. **Identity/parent/physical location:** exact Unreal asset type, native/Blueprint inheritance, stable name, exact Content Browser path, relevant Source location, first creation/activation phase, and server/client/editor relevance.
2. **Purpose/boundaries:** what it does in beginner language, why separate, what must not own. Avoid Profile/GameInstance/WorldState and UI duplication.
3. **How to create:** exact Editor sequence or native class preparation with Unreal plugin/module dependencies, parents, components and settings. `Editor action`, `Unreal engine API`, `third-party plugin API`, `custom project function`, `illustrative pseudo-flow`, and `backend endpoint` must be explicitly distinguished.
4. **Properties/data:** field name, exact type, container shape/units, meaningful default/example, editability/Blueprint exposure, who can mutate, replication/persistence, schema validation and version impact. Never store authoritative Actor pointers in database snapshots.
5. **Commands and notifications:** actual or proposed function signatures, input/output/error, caller, validation, authoritative transaction, latency expectation, RPC/replication, change event, observers and cancellation behavior. The event signifies a completed change; it does not create the change merely because it was broadcast.
6. **Dependents/consumers:** prerequisites, exact active consumer assignments, reverse dependencies and sequence for bind/initialize/destroy/map/reconnect. Do not document a new resource recipe without stating which existing systems load and use it.
7. **Lifecycle and concurrency:** init, render/interaction, authority, death/cancel, zone handoff, teardown, saving, migration, full inventory/stale target/missing Data Asset, duplicate client requests and restart where relevant.
8. **Actual feature wiring:** one concrete input → C++/server validate → commit → replication/view → PaperZD/audio feedback → UI observer path. Include exact test map fixtures, error messages, latency/replay checks and acceptance results.
9. **Art/legal notes:** exact supplied archive relative path when relevant; missing animations/directions/equipment overlay combinations and provenance/licensing status.
10. **Troubleshooting and maturity:** frequent mistakes, conditions for safe deferral, known plugin/version uncertainties, related phase/system pages, definition-of-done. Do not label an Unreal class compiled unless a compiler actually ran.

**Architecture invariants:** authored definitions are immutable content; a runtime server actor projects but does not replace durable state; no cloned inventory model on equipment widgets; professions use data-driven composition instead of five independent gathering systems; crafting/build/quest/economy share server transaction primitives; animation drives presentation but not server results; a world contribution may not be counted twice by reconnect/zone transfer.

## 11. Required offline documentation repository structure

The target repository should resemble the original `game_docs` manual's navigable organization and editorial depth while reflecting the new 2D MMO. Use domain-specific folders only when they contain real pages/records. Example structure:

```
RPG_2D_Living_World_Development_Guide/
├── README.md
├── AGENTS.md
├── index.html
├── game-overview.html
├── getting-started.html
├── development-roadmap.html
├── architecture.html
├── first-vertical-slice.html
├── asset-index.html
├── dependency-map.html
├── ownership.html
├── feature-coverage.html
├── art-audit.html
├── plugin-audit.html
├── checklist.html
├── glossary.html
├── troubleshooting.html
├── sources-verification.html
├── design/
│   ├── vision-and-pillars.html
│   ├── vocational-identity.html
│   ├── combat-disciplines.html
│   ├── solo-to-30-contract.html
│   ├── living-regions.html
│   ├── world-and-story.html
│   ├── economic-balance.html
│   └── content-production.html
├── architecture/
│   ├── source-migration.html
│   ├── state-ownership.html
│   ├── multiplayer-session-plugin.html
│   ├── server-and-realm-topology.html
│   ├── transactions-and-ledgers.html
│   ├── identity-and-characters.html
│   ├── zone-transfers.html
│   ├── region-state-and-snapshots.html
│   ├── service-responsibilities.html
│   ├── persistence-and-migrations.html
│   └── error-recovery.html
├── phases/
│   ├── phase-00.html
│   ├── ...
│   └── phase-31.html
├── systems/
│   ├── index.html
│   ├── ... one linked implementation chapter per committed subsystem
├── professions/
│   ├── index.html
│   ├── forgekeeper.html
│   ├── hearthkeeper.html
│   ├── wayfinder.html
│   ├── woodwright.html
│   └── apothecary.html
├── world/
│   ├── world-map-and-travel.html
│   ├── authored-biomes.html
│   ├── living-region-stages.html
│   ├── resource-sites.html
│   ├── narrative-content-pipeline.html
│   └── ... concrete zone/settlement/dungeon pages
├── art/
│   ├── source-inventory.html
│   ├── paper2d-import.html
│   ├── paperzd-directions.html
│   ├── equipment-visual-matrix.html
│   ├── environment-tiles-and-y-sorting.html
│   └── missing-art-backlog.html
├── multiplayer/
│   ├── plugin-compatibility.html
│   ├── session-and-login.html
│   ├── dedicated-servers.html
│   ├── zones-and-reconnect.html
│   ├── state-replication.html
│   ├── persistence-and-security.html
│   ├── population-scaling.html
│   └── operations-and-testing.html
├── engineering/
│   ├── index.html
│   └── ... C++ and Blueprint standards, native contract pages and code review
├── assets/
│   ├── Core/ Player/ CharacterCreation/ Vocations/ Input/ UI/
│   ├── World/ Regions/ Maps/ Art/ Animation/ Enemies/ Combat/
│   ├── Abilities/ Effects/ Progression/ Talents/ Inventory/
│   ├── Items/ Loot/ Equipment/ Resources/ Gathering/ Fishing/
│   ├── Farming/ Cooking/ Crafting/ Quests/ NPCs/ Economy/
│   ├── Merchants/ Parties/ Guilds/ Network/ Persistence/ Tests/
│   └── ... additional actual registered folder mirrors
├── sources/
│   ├── current-asset-manifest.json
│   ├── phase-creation-order.json
│   ├── dependency-edges.json
│   ├── phase-integration.json
│   ├── system-coverage.json
│   ├── feature-coverage.json
│   ├── design-decisions.json
│   ├── profession-loops.json
│   ├── region-state-contracts.json
│   ├── source-art-inventory.csv
│   ├── plugin-audit.json
│   └── verification.json
├── site/
│   ├── style.css
│   ├── app.js
│   └── search-data.js
└── tools/
    ├── build_manual_indexes.py
    ├── validate_documentation.py
    ├── check_phase_integration.py
    └── check_feature_coverage.py
```

The `assets/` documentation pages must mirror the planned actual Unreal `Content/Game/...` domain allocation; native types must show their intended `Source/RPG/...` placement separately. The above tree is an example, **not** an invitation to create empty placeholder folders or copy source `game_docs` classes unchanged. Use a validated target directory tree from the canonical manifest. Keep a stable naming convention and exactly one registered identity/path per asset.

### 11.1 Offline-first website and editing workflow

- Open `index.html` directly from local storage; relative links work without any web server or internet. Use no CDN JS/CSS, remote fonts or runtime `fetch()` of local JSON that fails under common `file://` policies. Embedded or pre-generated JS search indexes are acceptable. External documentation links are references only.
- Accessible responsive sidebar, system/phase/vocation navigation, searchable asset index, filters, glossary terms at point of use, reverse dependency links, 'what to create now' tables, beginner instructions, breadcrumb navigation and contrast-appropriate light/dark presentation.
- Import/export completion checkmarks as explicit JSON with schema version; localStorage persistence is opportunistic and should not be confused with game persistence. Export before changing browsers or docs versions.
- Generate repeated indices, asset dependency reverse users, phase counts, search records, feature coverage and page summaries from source registries; do not hand-edit generated blocks. `AGENTS.md` details source edits → generation → link/invariant validation and error reporting.
- Every cross-link must resolve. Provide content audit scripts detecting missing/unregistered assets, duplicate IDs, malformed folder paths, mismatched reverse dependencies, cycles in asset creation order, invalid phase numbering, inaccessible orphan pages, features with no implementation chapter, incomplete solo acceptance cases, missing domain owner and `verified` statuses lacking actual evidence.
- Browser and editor tests are separate: static validation can establish completeness of links/registries; it does not prove dynamic UI, Blueprints, Unreal compilation or network operation. Record real commands and results, with explicit not-run flags.

## 12. Teaching standard and quality controls

Explain concepts when first introduced: Actor, Character/Pawn, Component, interface, GameMode/GameState/PlayerState/Controller/GameInstance, server RPC, replicated properties, ownership, local prediction, authoritative server, Data Assets and instanced items, Tags/GAS effects, Paper2D flipbooks, PaperZD animation graph, TileSets/TileMaps, UMG focus, backend storage, transactions, durable receipts, idempotency, content migration, zone transfer, session lease, contribution meter, and input accessibility. Write plain-language purpose first, then exact technical instructions.

Every feature chapter must distinguish **definition** vs **runtime actor/instance** vs **persisted value** vs **UI/animation projection**. A student should be able to answer: where does it live, who owns it, who is allowed to change it, how is it displayed, when does it save, how does it recover, what failed request looks like, what art exists, what was actually tested?

Favor correct minimal systems and maintainable code plans: clear ownership and single source of truth, descriptive names, shallow hierarchy, composition where it helps, C++ native stable APIs and Blueprint-exposed authoring, meaningful event delegates, explicit lifecycle and initialization, no arbitrary global manager bloat, no repeated code for five vocations. Test fragile boundaries before adding content. Avoid engine speculation, pseudo-API presented as official, and overengineering for unmeasured thousands of players.

Give target-test acceptance criteria, not ungrounded guarantees. Include exact configuration where verified and label examples as illustrative where version-specific. All remote/Steam/dedicated-session assumptions must be confirmed against the installed Unreal version and third-party plugin build; document verification commands and expected observations without claiming execution unless performed.

## 13. Reference documents and version checks

Version-check relevant official Unreal docs and installed API signatures for the actual target engine. At minimum provide reference links to:

- `https://dev.epicgames.com/documentation/en-us/unreal-engine/paper-2d-overview-in-unreal-engine`
- `https://dev.epicgames.com/documentation/en-us/unreal-engine/paper-2d-flipbooks-in-unreal-engine`
- `https://dev.epicgames.com/documentation/en-us/unreal-engine/online-subsystem-session-interface-in-unreal-engine`
- `https://dev.epicgames.com/documentation/en-us/unreal-engine/setting-up-dedicated-servers-in-unreal-engine`
- `https://dev.epicgames.com/documentation/en-us/unreal-engine/networking-overview-for-unreal-engine`
- `https://dev.epicgames.com/documentation/en-us/unreal-engine/understanding-the-unreal-engine-gameplay-ability-system`
- `https://dev.epicgames.com/documentation/en-us/unreal-engine/travelling-in-multiplayer-in-unreal-engine`
- `https://dev.epicgames.com/documentation/en-us/unreal-engine/online-subsystem-steam-interface-in-unreal-engine`

Treat 5.8.x docs and the installed PaperZD/MultiplayerSessions binaries/code as separate evidence. Legacy Online Subsystem and newer Online Services are not drop-in identical. Steam lobby presence settings for a player-hosted listen game are not automatically suitable for dedicated persistent servers. No session plugin inherently supplies databases, world-project persistence, cross-zone migration or guild services. Record plugin/module build and packaging results **only if you actually run them**.

## 14. Completion/acceptance contract for the generated guide

The guide can be called **complete only** when every condition below is met:

1. A **new repo or packaged directory** exists, independent of original `game_docs`, with a working offline `index.html`, checked relative links, real linked HTML pages and delivered ZIP.
2. `sources/current-asset-manifest.json` registers every required game-facing asset with one canonical identity and implementation page; direct/reverse dependencies, owner, folder, activation phase and provenance agree across pages.
3. Every committed feature in Sections 3–8 is included in `feature-coverage.json`, has a full system chapter, a creation/integration phase, an actual owner and concrete solo/two-client tests. The five vocations each have gameplay flows, mastery and world impacts; no vocation degenerates into only repeat-click harvesting.
4. Every Phase 00–31 has explicit create/compile/configure/connect/map-edit/test instructions, acceptance/rejection/regression checks, art and architecture caveats, and a clear stop condition. All new assets have actual consumers rather than disconnected shell definitions.
5. A dedicated **solo-to-30 parity specification** exists with test cases for populations 1,2,5,10,30; core narrative/world/profession/combat milestones can be completed by one person with published alternatives and without forced human trade. NPC aid and adaptive scaling do not enable AFK farming or double rewards.
6. Living Regions tracks settlement construction, threat and discovery with durable server-ledger rules, visual stage changes, multiple vocation contributions, solo alternate paths, idempotent updates, reconnect and safe restart/season policies. New arrivals observe the authoritative state.
7. The delivered architecture describes a genuine authoritative MMO-style server with durable identity/character/vocation/equipment/region/quest states and per-character zone transfer, **not** a listen server and local `SaveGame` described as a persistent MMO.
8. The uploaded `MultiplayerSessions` source receives its own verifiable gap/compatibility assessment; do not hide empty stubs, host-only assumptions, untested 5.8.3 compatibility, provider-specific requirements or incomplete callbacks. The docs document how/when it can be safely used or replaced.
9. Supplied sprite sheets are accurately inventoried and their source names, four-direction limitations, layer/animation compatibility, missing eight-direction art and missing environment content are clear. **No paid assets or plugin binaries are redistributed** without confirmed rights.
10. There are no false engine-node names, fake compiler/runtime tests, invented services, contradictions about profession choice/solo play/2D world, or missing references to crucial dependencies and fail states. C++ vs Blueprint responsibility and authoring boundaries remain consistent.
11. Documentation generators, manifest checks, link validation, and feature coverage checks run with reproducible results. State exact commands passed/failed/not run, actual content/page/asset/phase counts and remaining blockers.
12. Full guide includes original fantasy world content and a reproducible biome/quest/profession content-creation pipeline, not only engine architecture or empty design headings.

### Failure and partial-delivery rule

If input files, remote repo access, engine validation or output capacity are unavailable, **say so explicitly**. Deliver a truthful partial package with its actual scope, unresolved cases, and next required work. Do not substitute an outline for finished pages while claiming complete coverage. Never state Unreal/game/network tests passed based solely on reading source docs.
