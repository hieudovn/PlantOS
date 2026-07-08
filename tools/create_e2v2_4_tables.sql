CREATE TABLE IF NOT EXISTS edge_heartbeats (
    id UUID PRIMARY KEY,
    edge_node_id VARCHAR(128) NOT NULL REFERENCES edge_nodes(edge_node_id),
    status VARCHAR(32) DEFAULT 'online',
    backlog_count INTEGER DEFAULT 0,
    signal_count INTEGER DEFAULT 0,
    hostname VARCHAR(255),
    ip_address VARCHAR(45),
    edge_version VARCHAR(32),
    center_sync VARCHAR(32),
    disk_usage_mb FLOAT,
    capabilities JSONB DEFAULT '[]',
    connectors_json JSONB DEFAULT '[]',
    received_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_edge_heartbeats_node_rcv ON edge_heartbeats(edge_node_id, received_at DESC);
CREATE INDEX IF NOT EXISTS ix_edge_heartbeats_received_at ON edge_heartbeats(received_at DESC);

CREATE TABLE IF NOT EXISTS edge_connectors (
    id UUID PRIMARY KEY,
    edge_node_id VARCHAR(128) NOT NULL REFERENCES edge_nodes(edge_node_id),
    connector_id VARCHAR(128) NOT NULL,
    connector_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'unknown',
    signal_count INTEGER DEFAULT 0,
    last_error TEXT,
    last_success_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(edge_node_id, connector_id)
);
CREATE INDEX IF NOT EXISTS ix_edge_connectors_node ON edge_connectors(edge_node_id);

CREATE TABLE IF NOT EXISTS edge_commands (
    id UUID PRIMARY KEY,
    edge_node_id VARCHAR(128) NOT NULL REFERENCES edge_nodes(edge_node_id),
    command_type VARCHAR(64) NOT NULL,
    target VARCHAR(128),
    status VARCHAR(32) DEFAULT 'pending',
    requested_by VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    result_message TEXT
);
CREATE INDEX IF NOT EXISTS ix_edge_commands_node_status ON edge_commands(edge_node_id, status);
CREATE INDEX IF NOT EXISTS ix_edge_commands_pending ON edge_commands(status) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS edge_config_versions (
    id UUID PRIMARY KEY,
    edge_node_id VARCHAR(128) NOT NULL REFERENCES edge_nodes(edge_node_id),
    version INTEGER NOT NULL,
    config_hash VARCHAR(64),
    source VARCHAR(32) DEFAULT 'local',
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by VARCHAR(128),
    UNIQUE(edge_node_id, version)
);
CREATE INDEX IF NOT EXISTS ix_edge_cfgver_node ON edge_config_versions(edge_node_id);
