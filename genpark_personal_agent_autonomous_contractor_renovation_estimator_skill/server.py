# -*- coding: utf-8 -*-
"""MCP Server for Contractor Renovation Bidding Audit & Counter-Offer Estimator Skill."""
import sys
import json
import logging
from typing import Dict, Any

from .core import ContractorRenovationBiddingEstimator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOOLS_SCHEMA = [
    {
        "name": "audit_contractor_renovation_quote",
        "description": "Audit contractor line-item quote against fair market regional benchmarks, detecting excessive margins (>25%) and hidden scope padding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string"
                },
                "region_metro_code": {
                    "type": "string",
                    "description": "e.g. SF_BAY, NYC_METRO, NATIONAL_AVG"
                },
                "quote_total_usd": {
                    "type": "number"
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "trade": {
                                "type": "string",
                                "enum": [
                                    "demolition",
                                    "electrical",
                                    "plumbing",
                                    "framing",
                                    "drywall",
                                    "tile_flooring",
                                    "cabinets_millwork",
                                    "painting",
                                    "general_conditions"
                                ]
                            },
                            "quoted_cost_usd": {
                                "type": "number"
                            },
                            "square_footage": {
                                "type": "number"
                            }
                        },
                        "required": [
                            "trade",
                            "quoted_cost_usd"
                        ]
                    }
                }
            },
            "required": [
                "project_name",
                "quote_total_usd",
                "line_items"
            ]
        }
    },
    {
        "name": "synthesize_contractor_counter_bid",
        "description": "Generate an evidence-backed counter-bid negotiation dossier with rationalized target contract sum and payment milestone escrow schedule.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contractor_name": {
                    "type": "string"
                },
                "original_quote_usd": {
                    "type": "number"
                },
                "audited_fair_market_usd": {
                    "type": "number"
                },
                "target_counter_offer_usd": {
                    "type": "number"
                },
                "flagged_trades": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "contractor_name",
                "original_quote_usd",
                "audited_fair_market_usd",
                "target_counter_offer_usd"
            ]
        }
    }
]

def handle_rpc(line: str) -> str:
    try:
        req = json.loads(line)
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            res = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "genpark-personal-agent-autonomous-contractor-renovation-estimator-skill", "version": "1.0.0"}
            }
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": res})

        elif method == "tools/list":
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS_SCHEMA}})

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})

            target_func = getattr(ContractorRenovationBiddingEstimator, tool_name, None)
            if not target_func:
                return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {tool_name}"}})

            result = target_func(**args)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }
            })

        else:
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})

    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "id": req.get("id") if "req" in locals() else None, "error": {"code": -32000, "message": str(e)}})

def run_test():
    print("[TEST] Running internal RPC self-test for genpark-personal-agent-autonomous-contractor-renovation-estimator-skill...")
    init_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    init_res = json.loads(handle_rpc(init_req))
    assert init_res.get("result", {}).get("serverInfo", {}).get("name") == "genpark-personal-agent-autonomous-contractor-renovation-estimator-skill"

    list_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    list_res = json.loads(handle_rpc(list_req))
    assert len(list_res.get("result", {}).get("tools", [])) == 2
    print(f"[TEST] SUCCESS: {len(list_res['result']['tools'])} tools verified.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        if run_test():
            sys.exit(0)
        sys.exit(1)

    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
