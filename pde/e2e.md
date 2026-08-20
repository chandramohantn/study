Let's make everything concrete with a full verification workflow for the **1D heat equation**.

We will go from:

$$
\text{physics} \rightarrow \text{PDE} \rightarrow \text{IC/BC} \rightarrow \text{discretization} \rightarrow \text{numerical solution} \rightarrow \text{error analysis} \rightarrow \text{mesh/time convergence} \rightarrow \text{conservation check}.
$$

## 1. Define the physical problem

Consider a thin rod of length $L=1$. Let $u(x,t) $ represent temperature.

Assume heat conduction only, no internal heat generation.

The PDE is

$$
\frac{\partial u}{\partial t} = \alpha \frac{\partial^2u}{\partial x^2}, \qquad 0<x<1.
$$

For simplicity set $\alpha=1$. So:

$$
\boxed{u_t=u_{xx}}
$$

---

## 2. Choose boundary conditions

Let's keep both ends fixed at zero temperature:

$$
u(0,t)=0, \qquad u(1,t)=0
$$

These are Dirichlet boundary conditions.

Physically, imagine the rod ends connected to large thermal reservoirs maintained at the reference temperature.

---

## 3. Choose an initial condition

Let $u(x,0)=\sin(\pi x)$. So initially the temperature looks like:

```text
temperature

 /\
 / \
 / \

----/------\----

0 1
```

More precisely:

$$
u(0,0)=0,
$$

$$
u(0.5,0)=1,
$$

$$
u(1,0)=0
$$
This choice is deliberate because the exact solution is known.

---

## 4. Exact analytical solution

For this particular problem,

$$
\boxed{ u(x,t) = e^{-\pi^2t}\sin(\pi x) }
$$

is the exact solution.

Let's verify it.

Calculate:
$$
u_t = -\pi^2 e^{-\pi^2t} \sin(\pi x)
$$
And:
$$
u_{xx} = -\pi^2 e^{-\pi^2t} \sin(\pi x)
$$
Therefore:

$$
u_t=u_{xx}
$$

Boundary conditions:

$$
u(0,t)=0,
$$

because $\sin 0=0,$. and $u(1,t)=0,$. because $\sin\pi=0$. Initial condition:

$$
u(x,0) = \sin(\pi x)
$$

Everything matches.

This exact solution gives us a ground truth against which to test the numerical solver.

---

## 5. What does the physical solution do?

Notice:

$$
u(x,t) = e^{-\pi^2t}\sin(\pi x)
$$
The spatial shape stays sinusoidal.

Its amplitude decreases exponentially.

At (t=0):

$$
u(x,0)=\sin(\pi x)
$$

At later time:

$$
u(x,t) = \underbrace{e^{-\pi^2t}}_{\text{shrinking amplitude}} \sin(\pi x)
$$
So physically:

```text
t = 0
 /\
 / \
_____/____\_____

t = 0.05
 /\
_____/__\______

t = 0.2
 /\
____/ \_______

eventually

________________
```

The rod cools because heat escapes through the boundaries.

---

## 6. Spatial discretization

Divide the rod into (N) intervals.

Grid spacing:

$$
\Delta x=\frac{1}{N}
$$

Grid points:

$$
x_i=i\Delta x
$$
Let u_i^n  approximate u(x_i,t_n) The second derivative becomes:
$$
u_{xx}(x_i,t_n) \approx \frac{ u_{i-1}^n - 2u_i^n + u_{i+1}^n }{ \Delta x^2 }
$$
---

## 7. Time discretization

Use forward Euler:
$$
u_t \approx \frac{ u_i^{n+1}-u_i^n }{ \Delta t }
$$
Insert both approximations into:

$$
u_t=u_{xx}
$$

We get:

$$
\frac{ u_i^{n+1}-u_i^n }{ \Delta t } = \frac{ u_{i-1}^n - 2u_i^n + u_{i+1}^n }{ \Delta x^2 }
$$

Rearrange:

$$
\boxed{ u_i^{n+1} = u_i^n + r \left( u_{i-1}^n - 2u_i^n + u_{i+1}^n \right) }
$$

where $r=\frac{\Delta t}{\Delta x^2}$. This is our numerical solver.

---

## 8. Initializing the solver

At (t=0):

$$
u_i^0 = \sin(\pi x_i)
$$
For example, suppose:

$$
N=4
$$

Then:

$$
\Delta x=0.25
$$
Points:

$$
x= [0,0.25,0.5,0.75,1]
$$

Initial temperatures:

$$
u^0= [ 0, \sin(\pi/4), 1, \sin(3\pi/4), 0 ]
$$

Approximately:

$$
u^0= [ 0, 0.7071, 1, 0.7071, 0 ]
$$

Boundary values are fixed:

$$
u_0^n=0, \qquad u_N^n=0
$$
---

## 9. Stability check

For this explicit heat solver, stability requires:

$$
\boxed{ r=\frac{\Delta t}{\Delta x^2}\leq\frac12 }
$$

$$
in 1D. Suppose:
$$

$$
\Delta x=0.1
$$

Then:

$$
\Delta x^2=0.01
$$
So:

$$
\Delta t \leq 0.005
$$

Choose:

$$
\Delta t=0.004
$$
Then:

$$
r=0.4
$$

Stable.

If instead:

$$
\Delta t=0.02,
$$

then:

$$
r=2
$$
The simulation is likely to become unstable.

---

## 10. One timestep manually

Suppose again:
$$
u^0= [ 0, 0.7071, 1, 0.7071, 0 ]
$$
Let:

$$
r=0.4
$$
$$
At interior node (i=1):
$$
$$
u_1^1 = u_1^0 + 0.4 ( u_0^0 - 2u_1^0 + u_2^0 )
$$

Substitute:

$$
u_1^1 = 0.7071 + 0.4 ( 0 - 2(0.7071) + 1 )
$$

So:

$$
u_1^1 \approx 0.5414
$$
$$
At (i=2):
$$
$$
u_2^1 = 1 + 0.4 ( 0.7071 - 2 + 0.7071 )
$$
Therefore:

$$
u_2^1 \approx 0.7657
$$

Notice what happened:

$$
0,;0.707,;1,;0.707,;0
$$

became approximately

$$
[0,;0.541,;0.766,;0.541,;0]
$$
The temperature profile is decaying exactly as expected physically.

---

## 11. Now ask the first verification question

Did we solve the **discrete equations** correctly?

Given the update equation:
$$
u_i^{n+1} - u_i^n - r \left( u_{i-1}^n - 2u_i^n + u_{i+1}^n \right) = 0,
$$
define a residual:
$$
R_i^n = u_i^{n+1} - u_i^n - r (u_{i-1}^n - 2u_i^n + u_{i+1}^n)
$$
For a correctly implemented explicit method, this should be close to machine precision:

$$
R_i^n\approx0
$$

But remember:

$$
R\approx0
$$

only tells us that we solved our **discrete numerical equations**.

It does not yet prove that they approximate the PDE well.

---

## 12. Compare directly against exact solution

Suppose we want the temperature at:

$$
T=0.1
$$
The exact solution is:

$$
u_{\text{exact}}(x,0.1) = e^{-0.1\pi^2}\sin(\pi x)
$$

Since:

$$
e^{-0.1\pi^2} \approx0.3727,
$$

the exact peak at (x=0.5) is:

$$
u(0.5,0.1)\approx0.3727
$$
If the numerical solver gives:

$$
u_h(0.5,0.1)=0.376,
$$

then pointwise error is:

$$
e = |0.376 - 0.3727| = 0.0033
$$

Relative error:

$$
\frac{0.0033}{0.3727} \approx0.89%
$$
Now we have an actual accuracy measurement.

---

## 13. But checking one point isn't enough

We want an error over the whole domain.

One common metric is discrete (L^2) error:

$$
E_{L^2} = \sqrt{ \Delta x \sum_i \left( u_i-u_{\text{exact}}(x_i) \right)^2 }.
$$

Another is maximum error:

$$
E_\infty = \max_i | u_i-u_{\text{exact}}(x_i) |.
$$

These answer different questions.

### (L^2) error

Measures average global error.

### (L^\infty) error

Measures the worst local error.

Both are useful.

---

## 14. Spatial mesh-refinement study

Now perform the same simulation using:

$$
N=20,\quad40,\quad80,\quad160
$$

Therefore:

$$
\Delta x= 0.05,; 0.025,; 0.0125,; 0.00625
$$

Suppose the errors look like:

| (\Delta x) | (L^2) error |
| ---------: | -----------------: |
| 0.05 | (2.1\times10^{-3}) |
| 0.025 | (5.3\times10^{-4}) |
| 0.0125 | (1.3\times10^{-4}) |
| 0.00625 | (3.3\times10^{-5}) |

Every time we halve (\Delta x), error decreases by about (4).

That suggests:

$$
E\propto\Delta x^2
$$
So observed spatial order is:

$$
p\approx2
$$

Exactly what we expect from the centered second derivative.

This is strong evidence that the spatial discretization is behaving correctly.

---

## 15. But our time method is only first order

Forward Euler has time truncation error:

$$
O(\Delta t)
$$
So total error behaves approximately like:
$$
E = C_x\Delta x^2 + C_t\Delta t
$$
This creates an important issue.

Suppose you refine:

$$
\Delta x
$$

but keep \Delta t  fixed.

Eventually spatial error becomes tiny, but temporal error dominates.

Then you won't observe second-order spatial convergence anymore.

So when doing a spatial convergence study, you need to make temporal error sufficiently small.

---

## 16. Time-refinement study

Keep the spatial mesh very fine.

Then solve using:
$$
\Delta t = 0.004, 0.002, 0.001, 0.0005
$$
Suppose errors are:

| (\Delta t) | Error |
| ---------: | -----------------: |
| 0.004 | (1.6\times10^{-3}) |
| 0.002 | (8.0\times10^{-4}) |
| 0.001 | (4.0\times10^{-4}) |
| 0.0005 | (2.0\times10^{-4}) |

Each halving reduces error by approximately (2).

Thus:

$$
E\propto\Delta t
$$

Observed temporal order:

$$
p_t\approx1
$$
That matches forward Euler theory.

---

## 17. Observed order calculation

Suppose:

$$
E_h=2.1\times10^{-3}
$$

and E_{h/2}=5.3\times10^{-4}. Then:
$$
p = \frac{ \log(E_h/E_{h/2}) }{ \log2 }.
$$

Approximately:

$$
p = \frac{ \log(3.96) }{ \log2 } \approx1.99
$$

Excellent.

This is exactly the kind of evidence numerical analysts look for.

---

## 18. Now test instability deliberately

Suppose:

$$
\Delta x=0.05
$$
Then:

$$
\Delta x^2=0.0025
$$

The stability limit is:

$$
\Delta t\leq0.00125
$$
Now choose:

$$
\Delta t=0.01
$$

Then:

$$
r=4
$$
Initially, the solution might appear reasonable.

Then tiny floating-point or discretization perturbations begin growing:

```text
t0:
0.7 1.0.7 0

later:
0.4.7.4 0

later:
0 -.3 2.1 -.3 0

later:
0 8 -14 8 0

later:
0 -200 350 -200 0
```

The underlying physical PDE is stable.

The **numerical algorithm** is unstable.

This is a critical distinction.

---

## 19. Conservation check

Our current Dirichlet problem is not energy-conserving because heat leaves through the boundaries.

So let's temporarily switch to insulated boundaries:

$$
u_x(0,t)=0, \qquad u_x(1,t)=0
$$

Then total heat should be constant:

$$
Q(t)=\int_0^1u(x,t),dx
$$
Numerically:

$$
Q_h^n \approx \sum_i u_i^n\Delta x
$$

Compute:

$$
Q_h^0, Q_h^1,Q_h^2,\dots
$$

and define conservation error:

$$
\epsilon_Q(t) = \frac{ |Q_h(t)-Q_h(0)| }{ |Q_h(0)| }
$$

Suppose:

$$
Q_h(0)=0.63662
$$

and after simulation:

$$
Q_h(T)=0.63659
$$
Then:

$$
\epsilon_Q \approx4.7\times10^{-5}
$$

Very good.

If instead:

$$
Q_h(T)=0.54,
$$

something is suspicious.

---

## 20. But conservation doesn't replace convergence

Suppose two solvers produce:

### Solver A $Q(T)=Q(0)$ exactly.

But:

$$
E_{L^2}=10^{-1}
$$
### Solver B

Conservation error:

$$
10^{-5}
$$

and:

$$
E_{L^2}=10^{-4}
$$

Solver B is clearly more accurate.

A solver can preserve one global invariant while still producing a bad spatial solution.

So conservation is a diagnostic, not the whole verification story.

---

## 21. A full verification table

For a serious simulation, you might record something like:

| Test | Result |
| -------------------- | ------------------ |
| Discrete residual | (<10^{-10}) |
| Spatial convergence | (p_x=1.98) |
| Temporal convergence | (p_t=1.01) |
| Max error | (3.2\times10^{-4}) |
| (L^2) error | (1.1\times10^{-4}) |
| Conservation error | (4\times10^{-5}) |
| Stability constraint | satisfied |
| Analytical benchmark | matched |

Now “the solver works” means something measurable.

---

## 22. Verification workflow in practice

A robust PDE workflow often looks like this:

```text
Implement PDE
 ↓
run simple analytical benchmark
 ↓
check residuals
 ↓
mesh refinement
 ↓
measure spatial convergence rate
 ↓
time refinement
 ↓
measure temporal convergence rate
 ↓
check conservation
 ↓
test difficult regimes
 ↓
compare to trusted benchmark
 ↓
move to real geometry/problem
```

You do not begin with the most complicated real problem.

That's analogous to software engineering:

$$
\text{unit tests} \rightarrow \text{integration tests} \rightarrow \text{production system}.
$$

---

## 23. Manufactured solutions fit naturally here

Suppose your actual equation is:

$$
u_t + u u_x = \nu u_{xx} + f(x,t)
$$

Finding an exact analytical solution may be difficult.

Instead, choose:

$$
u_{\text{manufactured}} = e^{-t}\sin(\pi x)
$$
Compute:
$$
f(x,t) = u_t + uu_x - \nu u_{xx}
$$
Now by construction:

$$
u_{\text{manufactured}}
$$

is an exact solution of the modified PDE.

Run your solver.

Then test:

$$
|u_h-u_{\text{manufactured}}|
$$

This verifies:

* time derivative implementation,
* nonlinear term,
* diffusion term,
* boundary treatment,
* source term,
* discretization order.

MMS is essentially a very sophisticated PDE **unit test**.

---

## 24. Solver verification vs solution verification

These terms are sometimes distinguished.

## Code verification

Question:

> Is my implementation mathematically correct?

Use:

* analytical solutions,
* manufactured solutions,
* convergence-order tests.

## Solution verification

Question:

> How much numerical uncertainty exists in this particular simulation?

Use:

* mesh refinement,
* timestep refinement,
* Richardson extrapolation,
* residuals,
* conservation diagnostics.

This distinction is useful for engineering workflows.

---

## 25. Now suppose no analytical solution exists

This is the common industrial situation.

For something like realistic Navier-Stokes around complex equipment:

$$
u_{\text{exact}}
$$

is unknown.

Then trust is built indirectly.

You might do:

$$
\boxed{ \begin{aligned} &\text{verified CFD implementation}\\ +&\text{mesh convergence}\\ +&\text{time convergence}\\ +&\text{conservation}\\ +&\text{benchmark comparison}\\ +&\text{experimental validation}. \end{aligned} }
$$

No single metric establishes correctness.

---

## 26. Verification and validation hierarchy

Think of it as accumulating evidence:

```text
 Reality
 ▲
 │
 Experimental validation
 │
 Real simulation
 ▲
 │
 solution verification
 mesh / dt / conservation
 ▲
 │
 code verification
 MMS / analytical solutions
 ▲
 │
 numerical formulation
 ▲
 │
 PDE model
```

Each layer depends on the layers beneath it.

---

## 27. A very important engineering trap

Suppose your simulation has:

$$
\text{residual}=10^{-12}
$$
You may be tempted to report:

> “Simulation converged to (10^{-12}).”

That does **not** mean:

$$
\text{physical error}=10^{-12}
$$

You may have:

$$
\text{iterative error}=10^{-12}
$$

while:

$$
\text{mesh error}=5%
$$

and:

$$
\text{model error}=15%
$$
This distinction is routinely misunderstood.

A residual is not an accuracy estimate.

---

## 28. Another trap: overly fine mesh

You might think:

> Why not just use the smallest (\Delta x) possible?

Because cost explodes.

Suppose a 3D domain has:

$$
N^3
$$

cells.

Halving spacing in each dimension gives:

$$
(2N)^3=8N^3
$$

So you get roughly (8\times) more cells.

For an explicit diffusion problem, timestep may also need:

$$
\Delta t\rightarrow\frac{\Delta t}{4}
$$
Therefore total cost may increase roughly by:

$$
8\times4=32
$$

Just from halving the mesh spacing.

This is why numerical PDE work is fundamentally about **error versus computational cost**.

---

## 29. Adaptive refinement is an answer to this

Instead of refining everywhere:

```text
uniform:

||||||||||||||||||||||||||||||||||||
```

refine only where necessary:

```text
adaptive:

|----|----|--|-||||||||||-|----|----

 ↑
 sharp gradient
```

This tries to minimize:

$$
\text{computational cost}
$$

subject to:

$$
\text{error}<\epsilon
$$
That is a much more useful formulation than “use a fine mesh”.

---

## 30. This also gives us a useful bridge to ML

Think about a neural PDE surrogate.

Suppose it predicts:

$$
u_\theta(x,t)
$$

You should evaluate it against almost the same hierarchy:

### Equation residual

$$
R_{\text{PDE}} = u_t-\alpha u_{xx}
$$
### Boundary error

$$
R_{\text{BC}} = u_\theta(0,t)-g(t)
$$

### Initial-condition error

$$
R_{\text{IC}} = u_\theta(x,0)-u_0(x)
$$
### Conservation error

$$
R_{\text{cons}} = Q_\theta(t)-Q_\theta(0)
$$

### Reference-solver error

$$
|u_\theta-u_{\text{FEM}}|
$$
### Quantity-of-interest error

$$
|Q(u_\theta)-Q(u_{\text{reference}})|
$$

### Experimental error

$$
|u_\theta-u_{\text{experiment}}|
$$
So classical numerical-analysis thinking directly informs how Physics-AI models should be evaluated.

---

## 31. The most important takeaway from this entire section

There is no single number called “PDE solution correctness”.

Instead, you accumulate evidence:

$$
\boxed{ \begin{aligned} &\text{small iterative residual}\\ +&\text{expected mesh convergence}\\ +&\text{expected time convergence}\\ +&\text{appropriate stability behavior}\\ +&\text{conservation}\\ +&\text{benchmark agreement}\\ +&\text{experimental validation}\\ \Rightarrow&\text{confidence in simulation}. \end{aligned} }
$$

And importantly:

$$
\boxed{ \text{solver converged} \not\Rightarrow \text{solution is correct} }
$$

That principle is worth remembering.
