import random

from .constraints import validate


def route_distance(route, distance_matrix):
    total = 0

    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]

        total += distance_matrix[a][b]

    return total


def two_opt(solution, problem, fitness_function):

    best_solution = [route[:] for route in solution]

    best_score = fitness_function(
        best_solution,
        problem
    )

    improved = True

    while improved:
        improved = False

        for route_index in range(len(best_solution)):

            route = best_solution[route_index]

            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route) - 1):

                    candidate_solution = [
                        r[:] for r in best_solution
                    ]

                    candidate_route = candidate_solution[route_index]

                    candidate_route[i:j + 1] = reversed(
                        candidate_route[i:j + 1]
                    )

                    candidate_score = fitness_function(
                        candidate_solution,
                        problem
                    )

                    if candidate_score < best_score:

                        best_solution = candidate_solution
                        best_score = candidate_score
                        improved = True

    return best_solution, best_score

def two_opt_first_improvement(solution, problem, fitness_function):
    """
    First-improvement 2-opt.

    Accepts the first improving 2-opt move found rather than
    exhaustively searching the entire neighborhood for the best move.
    """

    best_solution = [route[:] for route in solution]

    best_score = fitness_function(
        best_solution,
        problem
    )

    improved = True

    while improved:
        improved = False

        for route_index in range(len(best_solution)):

            route = best_solution[route_index]

            for i in range(1, len(route) - 2):

                for j in range(i + 1, len(route) - 1):

                    candidate_solution = [
                        r[:] for r in best_solution
                    ]

                    candidate_route = candidate_solution[route_index]

                    candidate_route[i:j + 1] = reversed(
                        candidate_route[i:j + 1]
                    )

                    candidate_score = fitness_function(
                        candidate_solution,
                        problem
                    )

                    if candidate_score < best_score:

                        best_solution = candidate_solution
                        best_score = candidate_score

                        improved = True

                        # Immediately accept the first improvement.
                        break

                if improved:
                    break

            if improved:
                break

    return best_solution, best_score


def or_opt(solution, problem, fitness_function, segment_lengths=(1, 2, 3)):
    """
    Or-opt local search (first-improvement).

    Relocates short segments of 1-3 consecutive customers to a different
    position in the same route or a different route (including a
    different vehicle), optionally reversing the segment on insertion.

    Unlike 2-opt (which can only reverse a segment in place), Or-opt can
    move customers between routes and can jump orderings that a single
    segment reversal can never reach. This is what lets it escape 2-opt
    local optima such as a customer sitting in a locally-good-looking but
    globally suboptimal slot, and it is also the only one of the two
    moves that can fix a bad initial route partition.

    Like `two_opt_first_improvement`, this accepts the first improving
    move it finds and restarts the scan from there, rather than
    exhaustively ranking the whole neighborhood on every pass -- the
    Or-opt neighborhood (segment length x source position x destination
    route x destination position x orientation) is large enough that
    best-improvement search becomes impractically slow past a handful of
    customers.
    """

    best_solution = [route[:] for route in solution]

    best_score = fitness_function(
        best_solution,
        problem
    )

    improved = True

    while improved:
        improved = False

        for seg_len in segment_lengths:

            for src_route_index in range(len(best_solution)):

                src_route = best_solution[src_route_index]

                # Interior positions only -- never touch the depot bookends.
                # A segment of seg_len starting at `start` occupies indices
                # start .. start + seg_len - 1, which must all stay within
                # [1, len(src_route) - 2] (the depot bookends sit at index
                # 0 and len(src_route) - 1).
                for start in range(1, len(src_route) - seg_len):

                    end = start + seg_len  # exclusive

                    segment = src_route[start:end]

                    remainder = (
                        src_route[:start] + src_route[end:]
                    )

                    for dest_route_index in range(len(best_solution)):

                        dest_route = (
                            remainder
                            if dest_route_index == src_route_index
                            else best_solution[dest_route_index]
                        )

                        # Valid insertion gaps: after index i, for
                        # i in [0, len(dest_route) - 1), i.e. never
                        # after the closing depot.
                        for insert_at in range(1, len(dest_route)):

                            if (
                                dest_route_index == src_route_index
                                and insert_at == start
                            ):
                                # Same position -- no-op move.
                                continue

                            for segment_variant in (
                                (segment, list(reversed(segment)))
                                if seg_len > 1
                                else (segment,)
                            ):

                                candidate_solution = [
                                    r[:] for r in best_solution
                                ]

                                if dest_route_index == src_route_index:

                                    candidate_solution[src_route_index] = (
                                        remainder[:insert_at]
                                        + segment_variant
                                        + remainder[insert_at:]
                                    )

                                else:

                                    candidate_solution[src_route_index] = (
                                        remainder
                                    )

                                    candidate_solution[dest_route_index] = (
                                        dest_route[:insert_at]
                                        + segment_variant
                                        + dest_route[insert_at:]
                                    )

                                if not validate(candidate_solution, problem):
                                    continue

                                candidate_score = fitness_function(
                                    candidate_solution,
                                    problem
                                )

                                if candidate_score < best_score:

                                    best_solution = candidate_solution
                                    best_score = candidate_score
                                    improved = True

                                    # Immediately accept the first
                                    # improvement and restart the scan.
                                    break

                            if improved:
                                break

                        if improved:
                            break

                    if improved:
                        break

                if improved:
                    break

            if improved:
                break

    return best_solution, best_score


def local_search(solution, problem, fitness_function):
    """
    Combined 2-opt + Or-opt descent (a small variable-neighborhood search).

    Runs 2-opt to a local optimum, then Or-opt to a local optimum, and
    keeps alternating between the two as long as either one still finds
    an improvement. A solution that is 2-opt-optimal but not Or-opt-optimal
    (the exact failure mode of plain 2-opt getting stuck) will keep
    improving here until neither neighborhood has anything left to offer.
    """

    current_solution = [route[:] for route in solution]

    current_score = fitness_function(
        current_solution,
        problem
    )

    improved = True

    while improved:
        improved = False

        current_solution, two_opt_score = two_opt(
            current_solution,
            problem,
            fitness_function
        )

        if two_opt_score < current_score:
            current_score = two_opt_score
            improved = True

        current_solution, or_opt_score = or_opt(
            current_solution,
            problem,
            fitness_function
        )

        if or_opt_score < current_score:
            current_score = or_opt_score
            improved = True

    return current_solution, current_score


def double_bridge(solution):
    """
    Classic double-bridge 4-opt perturbation, adapted for multi-route VRP
    solutions.

    A double bridge cuts a tour into four pieces A-B-C-D and reconnects
    them as A-C-B-D. It is the standard "kick" used in iterated local
    search precisely because no sequence of 2-opt or Or-opt moves can
    undo it in a single step, so it reliably knocks a solution out of a
    2-opt/Or-opt local optimum without the destructive randomness of a
    pure random shuffle.

    When a single route is long enough (>= 8 stops, i.e. >= 6 customers)
    the bridge is applied within that route. Otherwise this falls back to
    swapping two random customers across two different routes, which
    serves the same "escape the current local optimum" purpose for small
    or heavily-partitioned instances.
    """

    candidate = [route[:] for route in solution]

    long_route_indices = [
        i for i, route in enumerate(candidate)
        if len(route) >= 8
    ]

    if long_route_indices:

        route_index = random.choice(long_route_indices)
        route = candidate[route_index]

        interior = route[1:-1]
        n = len(interior)

        # Pick three cut points splitting the interior into four
        # non-empty pieces: p1 | p2 | p3 | p4.
        cut_points = sorted(random.sample(range(1, n), 3))
        c1, c2, c3 = cut_points

        p1 = interior[:c1]
        p2 = interior[c1:c2]
        p3 = interior[c2:c3]
        p4 = interior[c3:]

        new_interior = p1 + p3 + p2 + p4

        candidate[route_index] = (
            [route[0]] + new_interior + [route[-1]]
        )

        return candidate

    # Fallback: swap one customer between two different non-empty routes.
    non_empty_indices = [
        i for i, route in enumerate(candidate)
        if len(route) > 2
    ]

    if len(non_empty_indices) < 2:
        return candidate

    route_a_index, route_b_index = random.sample(
        non_empty_indices, 2
    )

    route_a = candidate[route_a_index]
    route_b = candidate[route_b_index]

    pos_a = random.randint(1, len(route_a) - 2)
    pos_b = random.randint(1, len(route_b) - 2)

    route_a[pos_a], route_b[pos_b] = route_b[pos_b], route_a[pos_a]

    return candidate


def iterated_local_search(
    solution,
    problem,
    fitness_function,
    max_kicks=8,
    max_no_improve=4
):
    """
    Iterated Local Search (ILS): combined 2-opt + Or-opt descent, followed
    by repeated double-bridge kicks + re-descent, keeping the best
    feasible solution seen.

    This is the standard fix for the local-optimum trap described for the
    Hybrid QPSO + 2-opt algorithm: 2-opt alone can get stuck at an
    ordering that no single segment reversal can improve on, even though
    a relocate move (Or-opt) or a bigger structural jump (double bridge)
    would. Combining all three lets local search escape that trap while
    always keeping the best solution found, so it can never do worse
    than plain 2-opt.
    """

    best_solution, best_score = local_search(
        solution,
        problem,
        fitness_function
    )

    current_solution = best_solution
    no_improve_streak = 0

    for _ in range(max_kicks):

        if no_improve_streak >= max_no_improve:
            break

        kicked_solution = double_bridge(current_solution)

        if not validate(kicked_solution, problem):
            no_improve_streak += 1
            continue

        candidate_solution, candidate_score = local_search(
            kicked_solution,
            problem,
            fitness_function
        )

        if candidate_score < best_score:

            best_solution = candidate_solution
            best_score = candidate_score
            current_solution = candidate_solution
            no_improve_streak = 0

        else:

            no_improve_streak += 1
            # Keep exploring from the re-descended candidate even when it
            # didn't beat the incumbent, so consecutive kicks don't just
            # re-perturb the same already-explored local optimum.
            current_solution = candidate_solution

    return best_solution, best_score