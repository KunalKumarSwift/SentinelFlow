# Rego unit tests (`opa test deploy/opa`). The full cross-engine suite is
# tests/contracts/test_policy_engine_contract.py, run against a live OPA in CI.
package sentinelflow.authz_test

import rego.v1

import data.sentinelflow.authz

analyst := {"subject": "u-ana", "tenant_id": "acme", "team": "soc-emea", "roles": ["soc-analyst-l1"], "kind": "user"}

commander := {"subject": "u-cmdr", "tenant_id": "acme", "team": "soc-emea", "roles": ["incident-commander"], "kind": "user"}

incident := {"kind": "incident", "id": "inc-1", "tenant_id": "acme", "team": "soc-emea"}

ok_action := {"target_user": "alice", "proposer": "svc", "initiator": "u-ana", "prior_approvers": [], "approval_open": true, "quorum_met": false}

test_read_is_granted_by_role if {
	authz.decision == {"allowed": true, "reason": "granted by role soc-analyst-l1"} with input as {"principal": analyst, "permission": "incident:read", "resource": incident, "action": null}
}

test_other_tenant_is_denied_first if {
	other := object.union(incident, {"tenant_id": "globex"})
	authz.decision.reason == "resource belongs to another tenant" with input as {"principal": analyst, "permission": "incident:close", "resource": other, "action": null}
}

test_missing_permission if {
	authz.decision.reason == "missing permission incident:close" with input as {"principal": analyst, "permission": "incident:close", "resource": incident, "action": null}
}

test_approval_without_context_fails_closed if {
	authz.decision.reason == "approval requires action context" with input as {"principal": commander, "permission": "action:approve:high", "resource": incident, "action": null}
}

test_self_approval_is_denied if {
	self := object.union(ok_action, {"target_user": "u-cmdr"})
	authz.decision.reason == "cannot approve an action against yourself" with input as {"principal": commander, "permission": "action:approve:high", "resource": incident, "action": self}
}

test_valid_approval_is_allowed if {
	authz.decision.allowed with input as {"principal": commander, "permission": "action:approve:high", "resource": incident, "action": ok_action}
}

test_orchestrator_cannot_execute_without_quorum if {
	orch := object.union(analyst, {"subject": "svc-orchestrator", "roles": ["orchestrator"], "kind": "service"})
	authz.decision.reason == "approval quorum not met" with input as {"principal": orch, "permission": "action:execute", "resource": incident, "action": ok_action}
}
