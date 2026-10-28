# SentinelFlow authorisation: the same decisions and reasons as security/policy_engine.py.
#
# Order (first match wins, deny overrides): tenant boundary -> RBAC -> ABAC rules in the
# order of security/abac_rules.py DEFAULT_RULES -> allow naming the granting role.
# Role -> permission data comes from data.json, generated from security/roles.py.
package sentinelflow.authz

import rego.v1

approve_permissions := {"action:approve:low", "action:approve:medium", "action:approve:high"}

grants := {role |
	some role in input.principal.roles
	input.permission in data.sentinelflow.roles[role]
}

granting_role := min(grants) if count(grants) > 0

has_permission(permission) if {
	some role in input.principal.roles
	permission in data.sentinelflow.roles[role]
}

deny(reason) := {"allowed": false, "reason": reason}

decision := deny("resource belongs to another tenant") if {
	input.principal.tenant_id != input.resource.tenant_id
} else := deny(sprintf("missing permission %s", [input.permission])) if {
	count(grants) == 0
} else := deny(reason) if {
	reason := first_denial
} else := {"allowed": true, "reason": sprintf("granted by role %s", [granting_role])}

# ABAC rules, in DEFAULT_RULES order.
first_denial := reason if {
	reason := team_scope
} else := reason if {
	reason := approval_context
} else := reason if {
	reason := no_self_action
} else := reason if {
	reason := separation_of_duties
} else := reason if {
	reason := distinct_approvers
} else := reason if {
	reason := approval_still_open
} else := reason if {
	reason := executed_only_if_approved
}

team_scope := sprintf("resource belongs to team %s", [team]) if {
	team := input.resource.team
	team != null
	team != input.principal.team
	not has_permission("incident:read_all")
}

is_approval if input.permission in approve_permissions

# Approval rules fail closed when the action context is missing.
approval_context := "approval requires action context" if {
	is_approval
	input.action == null
}

no_self_action := "cannot approve an action against yourself" if {
	is_approval
	input.action.target_user == input.principal.subject
}

separation_of_duties := "separation of duties: proposer/initiator cannot approve" if {
	is_approval
	input.principal.subject in {input.action.proposer, input.action.initiator}
}

distinct_approvers := "you have already decided on this approval" if {
	is_approval
	input.principal.subject in input.action.prior_approvers
}

approval_still_open := "approval is no longer open" if {
	is_approval
	input.action.approval_open == false
}

executed_only_if_approved := "approval quorum not met" if {
	input.permission == "action:execute"
	not quorum_met
}

quorum_met if input.action.quorum_met == true
