package com.iflytek.stellar.console.toolkit.entity.core.workflow;

import lombok.Data;

@Data
public class Edge {
    String sourceNodeId;
    String targetNodeId;
    String sourceHandle;
    String targetHandle;
}
