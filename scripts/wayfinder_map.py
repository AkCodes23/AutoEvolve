"""AutoEvolve Wayfinder Decision Map Manager & Orchestrator.

Provides zero-dependency parsing, validation, frontier unblocking,
and Fog-of-War graduation for AutoEvolve v5.0 DIRECTION.md maps.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple


VALID_MODES = {'grilling', 'prototype', 'research', 'mutate'}


class WayfinderTicket:
    def __init__(
        self,
        ticket_id: str,
        title: str,
        mode: str,
        blocked_by: Optional[List[str]] = None,
        claimed_by: Optional[str] = None,
        signal: str = '',
        status: str = 'OPEN',
    ):
        self.ticket_id = ticket_id.strip()
        self.title = title.strip()
        self.mode = mode.strip().lower()
        self.blocked_by = blocked_by or []
        self.claimed_by = claimed_by
        self.signal = signal.strip()
        self.status = status.upper()

    def is_unblocked(self, resolved_ids: Set[str]) -> bool:
        if self.status != 'OPEN':
            return False
        return all(dep in resolved_ids for dep in self.blocked_by)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.ticket_id,
            'title': self.title,
            'mode': self.mode,
            'blocked_by': self.blocked_by,
            'claimed_by': self.claimed_by,
            'signal': self.signal,
            'status': self.status,
        }


class WayfinderMap:
    def __init__(self, destination: str = ''):
        self.destination = destination
        self.notes: List[str] = []
        self.active_frontier: List[WayfinderTicket] = []
        self.fog_of_war: List[str] = []
        self.out_of_scope: List[str] = []
        self.decisions_so_far: List[Dict[str, str]] = []
        self.hard_gates: List[str] = []
        self.soft_gates: List[str] = []

    @classmethod
    def parse_markdown(cls, md_text: str) -> WayfinderMap:
        wmap = cls()
        current_section = ''

        for line in md_text.splitlines():
            line_str = line.strip()
            if line_str.startswith('## '):
                header = line_str[3:].strip().lower()
                if 'destination' in header or 'objective' in header:
                    current_section = 'destination'
                elif 'frontier' in header:
                    current_section = 'frontier'
                elif 'fog' in header:
                    current_section = 'fog'
                elif 'out of scope' in header or 'anti-goal' in header:
                    current_section = 'out_of_scope'
                elif 'decisions' in header:
                    current_section = 'decisions'
                elif 'hard gate' in header:
                    current_section = 'hard_gates'
                elif 'soft gate' in header:
                    current_section = 'soft_gates'
                elif 'notes' in header:
                    current_section = 'notes'
                else:
                    current_section = ''
                continue

            if not line_str or line_str.startswith('<!--'):
                continue

            if current_section == 'destination':
                if not wmap.destination:
                    wmap.destination = line_str
                else:
                    wmap.destination += ' ' + line_str
            elif current_section == 'notes':
                if line_str.startswith('- '):
                    wmap.notes.append(line_str[2:].strip())
                else:
                    wmap.notes.append(line_str)
            elif current_section == 'frontier':
                if line_str.startswith('- ['):
                    is_done = line_str.startswith('- [x]') or line_str.startswith('- [X]')
                    after_bracket = line_str[5:].strip()
                    tid = ''
                    title = ''
                    params_str = ''
                    if after_bracket.startswith('['):
                        end_tid = after_bracket.find(']')
                        if end_tid != -1:
                            tid = after_bracket[1:end_tid].strip()
                            rest = after_bracket[end_tid+1:].strip()
                            if '(' in rest and rest.endswith(')'):
                                paren_idx = rest.rfind('(')
                                title = rest[:paren_idx].strip()
                                params_str = rest[paren_idx+1:-1].strip()
                            else:
                                title = rest
                    else:
                        title = after_bracket

                    mode = 'mutate'
                    blocked_by = []
                    claimed_by = None
                    signal = ''

                    if params_str:
                        for part in params_str.split(','):
                            if ':' in part:
                                k, v = part.split(':', 1)
                                k, v = k.strip().lower(), v.strip()
                                if k == 'mode':
                                    mode = v
                                elif k == 'blocked_by':
                                    clean_v = v.strip('[] ')
                                    if clean_v:
                                        blocked_by = [x.strip() for x in clean_v.split(';') if x.strip()]
                                elif k in ('claim', 'claimed_by'):
                                    claimed_by = v if v and v.lower() != 'none' else None
                                elif k == 'signal':
                                    signal = v

                    ticket = WayfinderTicket(
                        ticket_id=tid or f'F-{len(wmap.active_frontier)+1:02d}',
                        title=title or 'Untitled frontier step',
                        mode=mode,
                        blocked_by=blocked_by,
                        claimed_by=claimed_by,
                        signal=signal,
                        status='CLOSED' if is_done else 'OPEN',
                    )
                    wmap.active_frontier.append(ticket)
            elif current_section == 'fog':
                if line_str.startswith('- '):
                    wmap.fog_of_war.append(line_str[2:].strip())
                else:
                    wmap.fog_of_war.append(line_str)
            elif current_section == 'out_of_scope':
                if line_str.startswith('- '):
                    wmap.out_of_scope.append(line_str[2:].strip())
                else:
                    wmap.out_of_scope.append(line_str)
            elif current_section == 'decisions':
                if line_str.startswith('- ['):
                    end_b = line_str.find(']')
                    if end_b != -1 and '(' in line_str and '):' in line_str:
                        t_title = line_str[3:end_b].strip()
                        open_p = line_str.find('(', end_b)
                        close_p = line_str.find('):', open_p)
                        t_link = line_str[open_p+1:close_p].strip()
                        t_gist = line_str[close_p+2:].strip()
                        wmap.decisions_so_far.append({
                            'title': t_title,
                            'link': t_link,
                            'gist': t_gist,
                        })
                    else:
                        wmap.decisions_so_far.append({
                            'title': line_str[2:].strip(),
                            'link': '',
                            'gist': line_str[2:].strip(),
                        })
                elif line_str.startswith('- '):
                    wmap.decisions_so_far.append({
                        'title': line_str[2:].strip(),
                        'link': '',
                        'gist': line_str[2:].strip(),
                    })
            elif current_section == 'hard_gates':
                if line_str.startswith('- ') or re.match(r'^\d+\.', line_str):
                    clean = re.sub(r'^(?:-\s*|\d+\.\s*)', '', line_str).strip()
                    wmap.hard_gates.append(clean)
            elif current_section == 'soft_gates':
                if line_str.startswith('- ') or re.match(r'^\d+\.', line_str):
                    clean = re.sub(r'^(?:-\s*|\d+\.\s*)', '', line_str).strip()
                    wmap.soft_gates.append(clean)

        return wmap

    def get_resolved_ids(self) -> Set[str]:
        resolved = set()
        for t in self.active_frontier:
            if t.status == 'CLOSED':
                resolved.add(t.ticket_id)
        for d in self.decisions_so_far:
            t_match = re.match(r'\[?([^\]\s]+)\]?', d['title'])
            if t_match:
                resolved.add(t_match.group(1))
        return resolved

    def get_unblocked_frontier(self) -> List[WayfinderTicket]:
        resolved = self.get_resolved_ids()
        unblocked = []
        for t in self.active_frontier:
            if t.status == 'OPEN' and not t.claimed_by and t.is_unblocked(resolved):
                unblocked.append(t)
        return unblocked

    def claim_ticket(self, ticket_id: str, agent_id: str) -> bool:
        for t in self.active_frontier:
            if t.ticket_id == ticket_id:
                if t.status != 'OPEN':
                    return False
                if t.claimed_by and t.claimed_by != agent_id:
                    return False
                t.claimed_by = agent_id
                return True
        return False

    def resolve_ticket(self, ticket_id: str, decision_gist: str, link: str = '') -> bool:
        for t in self.active_frontier:
            if t.ticket_id == ticket_id:
                t.status = 'CLOSED'
                self.decisions_so_far.append({
                    'title': f'{t.ticket_id} {t.title}',
                    'link': link or f'file:///LINEAGE.md#{t.ticket_id}',
                    'gist': decision_gist,
                })
                return True
        return False

    def graduate_fog(self, fog_index: int, new_ticket: WayfinderTicket) -> bool:
        if 0 <= fog_index < len(self.fog_of_war):
            self.fog_of_war.pop(fog_index)
            self.active_frontier.append(new_ticket)
            return True
        return False

    def validate_invariants(self) -> Tuple[bool, List[str]]:
        errors = []
        if not self.destination:
            errors.append('Missing Destination in Wayfinder map')

        ticket_ids = set()
        for t in self.active_frontier:
            if t.ticket_id in ticket_ids:
                errors.append(f'Duplicate ticket ID in frontier: {t.ticket_id}')
            ticket_ids.add(t.ticket_id)

            if t.mode not in VALID_MODES:
                errors.append(f'Invalid mode for ticket {t.ticket_id}: {t.mode}. Must be one of {VALID_MODES}')

            if t.mode == 'grilling' and t.claimed_by and 'afk' in t.claimed_by.lower():
                errors.append(f'Grilling ticket {t.ticket_id} cannot be executed AFK; requires Human-in-the-loop (HITL)')

        return len(errors) == 0, errors

    def to_markdown(self) -> str:
        lines = ['# AutoEvolve Direction & Wayfinding Map', '']
        lines.append('## Destination')
        lines.append(f'{self.destination or "TBD"}')
        lines.append('')

        if self.notes:
            lines.append('## Notes')
            for n in self.notes:
                lines.append(f'- {n}')
            lines.append('')

        lines.append('## Active Frontier')
        for t in self.active_frontier:
            mark = 'x' if t.status == 'CLOSED' else ' '
            blocked_str = f'blocked_by: [{"; ".join(t.blocked_by)}]' if t.blocked_by else 'blocked_by: []'
            claim_str = f'claim: {t.claimed_by}' if t.claimed_by else 'claim: none'
            sig_str = f', signal: {t.signal}' if t.signal else ''
            lines.append(f'- [{mark}] [{t.ticket_id}] {t.title} (mode: {t.mode}, {blocked_str}, {claim_str}{sig_str})')
        lines.append('')

        lines.append('## Fog of War')
        if self.fog_of_war:
            for f in self.fog_of_war:
                lines.append(f'- {f}')
        else:
            lines.append('- *No uncharted fog remaining; ready for complete implementation.*')
        lines.append('')

        lines.append('## Out of Scope')
        if self.out_of_scope:
            for o in self.out_of_scope:
                lines.append(f'- {o}')
        else:
            lines.append('- *None.*')
        lines.append('')

        lines.append('## Decisions So Far')
        if self.decisions_so_far:
            for d in self.decisions_so_far:
                lnk = d.get('link', '')
                title = d.get('title', '')
                gist = d.get('gist', '')
                if lnk:
                    lines.append(f'- [{title}]({lnk}): {gist}')
                else:
                    lines.append(f'- {title}: {gist}')
        else:
            lines.append('- *No decisions recorded yet.*')
        lines.append('')

        if self.hard_gates:
            lines.append('## Hard Gates (must pass: binary)')
            for i, h in enumerate(self.hard_gates, 1):
                lines.append(f'{i}. {h}')
            lines.append('')

        if self.soft_gates:
            lines.append('## Soft Gates (should meet: proportional)')
            for s in self.soft_gates:
                lines.append(f'- {s}')
            lines.append('')

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='AutoEvolve Wayfinder Decision Map Manager')
    parser.add_argument('--map-file', default='DIRECTION.md', help='Path to DIRECTION.md map')
    parser.add_argument('--list-frontier', action='store_true', help='List unblocked frontier tickets')
    parser.add_argument('--claim', type=str, help='Ticket ID to claim')
    parser.add_argument('--agent-id', type=str, default='agent_swarm_1', help='Agent session ID')
    parser.add_argument('--validate', action='store_true', help='Validate map structure and invariants')
    args = parser.parse_args()

    if not os.path.exists(args.map_file):
        print(f'[FAIL] Map file not found: {args.map_file}')
        sys.exit(1)

    with open(args.map_file, 'r', encoding='utf-8') as f:
        content = f.read()

    wmap = WayfinderMap.parse_markdown(content)

    if args.validate:
        ok, errors = wmap.validate_invariants()
        if not ok:
            for err in errors:
                print(f'[FAIL] {err}')
            sys.exit(1)
        print('[PASS] Wayfinder map conforms to AutoEvolve v5.0 invariants.')

    if args.list_frontier:
        unblocked = wmap.get_unblocked_frontier()
        print(f'Unblocked Frontier ({len(unblocked)} tickets):')
        for t in unblocked:
            print(f'  - [{t.ticket_id}] {t.title} [mode={t.mode}] (signal: {t.signal or "N/A"})')

    if args.claim:
        if wmap.claim_ticket(args.claim, args.agent_id):
            with open(args.map_file, 'w', encoding='utf-8', newline='\n') as f:
                f.write(wmap.to_markdown())
            print(f'[PASS] Claimed ticket {args.claim} for agent {args.agent_id}')
        else:
            print(f'[FAIL] Could not claim ticket {args.claim}')
            sys.exit(1)


if __name__ == '__main__':
    main()
