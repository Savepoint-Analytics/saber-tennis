create schema if not exists tennis;

create table if not exists tennis.source_license (
    source_key text primary key,
    source_name text not null,
    source_url text not null,
    license_name text,
    license_url text,
    attribution_required boolean not null default true,
    non_commercial_only boolean not null default true,
    share_alike_required boolean not null default false,
    redistribution_allowed boolean,
    commercial_use_allowed boolean,
    status text not null default 'pending',
    notes text,
    verified_at timestamptz not null default now()
);

create table if not exists tennis.raw_manifest (
    manifest_id bigserial primary key,
    source_key text not null references tennis.source_license(source_key),
    snapshot_date date not null,
    source_commit_sha text,
    source_file_path text not null,
    minio_uri text not null,
    file_sha256 text not null,
    row_count bigint,
    acquired_at timestamptz not null default now(),
    acquired_by text not null default current_user,
    notes text,
    unique (source_key, snapshot_date, source_file_path, file_sha256)
);

insert into tennis.source_license (
    source_key,
    source_name,
    source_url,
    license_name,
    license_url,
    attribution_required,
    non_commercial_only,
    share_alike_required,
    redistribution_allowed,
    commercial_use_allowed,
    status,
    notes
)
values
('jeffsackmann_tennis_atp', 'Jeff Sackmann Tennis ATP', 'https://github.com/JeffSackmann/tennis_atp', 'CC BY-NC-SA 4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', true, true, true, false, false, 'target', 'Canonical ATP match/ranking source.'),
('jeffsackmann_tennis_wta', 'Jeff Sackmann Tennis WTA', 'https://github.com/JeffSackmann/tennis_wta', 'CC BY-NC-SA 4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', true, true, true, false, false, 'target', 'Canonical WTA match/ranking source.'),
('jeffsackmann_match_charting', 'Tennis Abstract Match Charting Project', 'https://github.com/JeffSackmann/tennis_MatchChartingProject', 'CC BY-NC-SA 4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', true, true, true, false, false, 'target', 'Shot-by-shot and point-level charting.'),
('jeffsackmann_slam_pointbypoint', 'Jeff Sackmann Grand Slam Point-by-Point', 'https://github.com/JeffSackmann/tennis_slam_pointbypoint', 'CC BY-NC-SA 4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', true, true, true, false, false, 'target', 'Grand Slam point data with varying schemas.'),
('jeffsackmann_pointbypoint', 'Jeff Sackmann Sequential Point-by-Point', 'https://github.com/JeffSackmann/tennis_pointbypoint', 'CC BY-NC-SA 4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', true, true, true, false, false, 'target', 'Compact point strings for simulation work.'),
('jeffsackmann_tennis_misc', 'Jeff Sackmann Tennis Misc', 'https://github.com/JeffSackmann/tennis_misc', 'CC BY-NC-SA 4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', true, true, true, false, false, 'reference', 'Algorithm reference only; do not vendor code.'),
('jeffsackmann_tennis_viz', 'Jeff Sackmann Tennis Viz', 'https://github.com/JeffSackmann/tennis_viz', 'Unclear for code; underlying data often CC BY-NC-SA 4.0', null, true, true, true, false, false, 'reference', 'Visualization reference only unless license is clarified.'),
('aneeshers_tennis_sackmann_archive', 'Aneeshers Tennis Sackmann Archive', 'https://github.com/Aneeshers/tennis-sackmann-archive', 'CC BY-NC-SA 4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/', true, true, true, false, false, 'fallback', 'Reviewed archival mirror for ATP/WTA/Slam point-by-point availability gaps. Use only with original Jeff Sackmann attribution and mirror provenance recorded.'),
('tennisabstract_atp_elo', 'Tennis Abstract ATP Elo', 'https://tennisabstract.com/reports/atp_elo_ratings.html', 'Tennis Abstract terms / attribution required', null, true, true, true, false, false, 'target', 'Benchmark/reference Elo snapshot.'),
('tennisabstract_wta_elo', 'Tennis Abstract WTA Elo', 'https://tennisabstract.com/reports/wta_elo_ratings.html', 'Tennis Abstract terms / attribution required', null, true, true, true, false, false, 'target', 'Benchmark/reference Elo snapshot.'),
('tennis_data_co_uk_unverified', 'Tennis-Data.co.uk', 'https://www.tennis-data.co.uk/', 'Terms unclear', null, true, true, false, false, false, 'isolated', 'Optional private odds benchmark only after terms review.'),
('tml_database_unverified', 'TML-Database', 'https://github.com/Tennismylife/TML-Database', 'Non-commercial unless permitted', null, true, true, false, false, false, 'isolated', 'Optional private evaluation only with lineage and terms review.')
on conflict (source_key) do update set
    source_name = excluded.source_name,
    source_url = excluded.source_url,
    license_name = excluded.license_name,
    license_url = excluded.license_url,
    attribution_required = excluded.attribution_required,
    non_commercial_only = excluded.non_commercial_only,
    share_alike_required = excluded.share_alike_required,
    redistribution_allowed = excluded.redistribution_allowed,
    commercial_use_allowed = excluded.commercial_use_allowed,
    status = excluded.status,
    notes = excluded.notes,
    verified_at = now();
