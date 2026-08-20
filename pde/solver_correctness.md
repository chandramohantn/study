This is the right next step, because in numerical PDEs the difficult question is often not:

> “Did the solver finish?”

but:

> “Did it solve the equations accurately enough that I should trust the result?”

The standard way to think about this is through **verification, convergence, stability, conservation, and validation**.

A very useful distinction is:

$$
\boxed{\text{Verification: did we solve the equations right?}}
$$

versus

$$
\boxed{\text{Validation: are these the right equations for reality?}}
$$

Those are different problems.

---

## 1. The true PDE solution is usually unknown

Suppose the continuous PDE is $\mathcal L(u)=f$. The exact solution is $u(x,t)$ But the computer returns a numerical approximation:

$$
u_h(x,t),
$$

where h represents mesh spacing.

If time is discretized too, we might write u_{h,\Delta t} What we really want to know is:
$$
|u-u_{h,\Delta t}|
$$
That would directly measure our error.

The problem is obvious:

> if we knew (u), we probably wouldn't need the numerical solver.

So numerical analysis gives us indirect ways to determine whether the approximation is approaching the unknown exact solution.

---

## 2. There are several different kinds of error

It's important not to lump all “solver error” together.

A numerical simulation can be wrong for many different reasons:

$$
\boxed{ \text{total error} = \text{modeling error} + \text{discretization error} + \text{iterative error} + \text{roundoff error} + \text{input uncertainty} }
$$

For example:

### Modeling error

You use incompressible Navier-Stokes when compressibility actually matters.

Even a perfect numerical solution would be physically wrong.

### Discretization error

You replace u_{xx}  with \frac{u_{i-1}-2u_i+u_{i+1}}{h^2} That approximation is not exact.

### Iterative error

You stop the linear/nonlinear solver before it fully converges.

### Roundoff error

Floating-point arithmetic introduces tiny errors.

Usually small, but not always negligible.

### Input uncertainty

Material parameters, geometry, boundary conditions, etc. may themselves be uncertain.

For now, let's focus on **numerical error**.

---

## 3. Consistency: does the discretization approximate the PDE correctly?

Start with the finite-difference approximation:

$$
u''(x_i) \approx \frac{u_{i-1}-2u_i+u_{i+1}}{h^2}
$$

Using Taylor expansion, one can show:

$$
\frac{u_{i-1}-2u_i+u_{i+1}}{h^2} = u''(x_i) + O(h^2).
$$

The term $O(h^2) $ is the **truncation error**.

It means that if you halve (h), $h \rightarrow \frac h2, $ the leading discretization error should decrease by roughly

$$
\left(\frac12\right)^2 = \frac14
$$

This method is therefore called **second-order accurate**.

Consistency means:

$$
\boxed{ \text{as }h,\Delta t\rightarrow0, \text{ the discrete equation approaches the original PDE} }
$$

If a discretization is inconsistent, making the grid finer will not necessarily recover the PDE.

---

## 4. Mesh refinement: the most important practical test

Suppose you solve the same problem using:

$$
h=0.1,
$$

then:

$$
h=0.05,
$$

then:

$$
h=0.025
$$
You get:

$$
u_{0.1},\quad u_{0.05},\quad u_{0.025}
$$

If the solutions look like:

$$
1.42,\quad1.31,\quad1.28,
$$

then they may be converging.

If instead:

$$
1.42,\quad2.87,\quad0.91,
$$

something is wrong or you are far from the asymptotic convergence region.

This gives the core practical idea:

$$
\boxed{ \text{refine the mesh and see whether the solution stops changing} }
$$

A trustworthy simulation should be sufficiently **grid-independent** for the quantities you care about.

---

## 5. Grid-independent does not mean pixel-identical

Suppose you are interested in drag coefficient:

$$
C_D
$$
You run:

| Mesh | Cells | (C_D) |
| ------ | ----: | ----: |
| Coarse | 100k | 0.347 |
| Medium | 400k | 0.326 |
| Fine | 1.6M | 0.321 |
| Finer | 6.4M | 0.320 |

Now you might conclude:

$$
C_D\approx0.320
$$

and the fine mesh is probably sufficient.

You don't necessarily care whether every local field value is identical.

Your convergence criterion should correspond to the **quantity of interest**, often called a QoI:

$$
Q(u)
$$

Examples:

* drag coefficient,
* maximum temperature,
* pressure drop,
* heat flux,
* stress concentration,
* integral mass flow.

This is a very important engineering principle:

$$
\boxed{ \text{mesh convergence should be assessed against the quantity you actually care about} }
$$

---

## 6. Richardson extrapolation

We can do better than “the values look close”.

Suppose your numerical solution behaves like:

$$
Q_h = Q_{\text{exact}} + Ch^p
$$
Here:

* (Q_h) = numerical result,
* (Q_{\text{exact}}) = unknown exact result,
* (p) = order of accuracy.

For a second-order scheme:

$$
p\approx2
$$

If we have two meshes with refinement ratio

$$
r=\frac{h_{\text{coarse}}}{h_{\text{fine}}},
$$

we can estimate:

$$
Q_{\text{exact}} \approx Q_{\text{fine}} + \frac{Q_{\text{fine}}-Q_{\text{coarse}}}{r^p-1}.
$$

This is **Richardson extrapolation**.

So instead of simply saying:

> “fine and medium are close”

we can estimate the limiting continuum value.

---

## 7. Observed order of convergence

Suppose you use three grids:

$$
h,\quad \frac h2,\quad \frac h4
$$
Compute solutions:

$$
Q_1,Q_2,Q_3
$$

Then the observed convergence order can be estimated as

$$
p \approx \frac{ \ln\left| \frac{Q_1-Q_2}{Q_2-Q_3} \right| }{ \ln 2 }.
$$

If your scheme is theoretically second order, you hope to see:

$$
p\approx2
$$
If you instead observe:

$$
p\approx0.3,
$$

you should investigate.

Possibilities include:

* mesh isn't fine enough yet,
* solution isn't smooth,
* boundary treatment is lower-order,
* numerical implementation is wrong,
* iterative solver error dominates,
* shocks/discontinuities are present.

This is a much stronger verification test than simply checking residuals.

---

## 8. Stability: do small errors remain controlled?

Consistency alone isn't enough.

A numerical method can approximate the PDE correctly locally and still become unstable globally.

Consider the heat equation:

$$
u_t = \alpha u_{xx}
$$

Using explicit Euler:

$$
u_i^{n+1} = u_i^n + \frac{\alpha\Delta t}{h^2} \left( u_{i-1}^n-2u_i^n+u_{i+1}^n \right).
$$

Define:

$$
r=\frac{\alpha\Delta t}{h^2}
$$
For the standard explicit scheme, stability requires:

$$
\boxed{r\leq\frac12}
$$

$$
in 1D. Suppose:
$$

$$
h=0.01
$$

If you make (\Delta t) too large, the numerical solution may start oscillating and then explode:

$$
1.0,;0.9,;1.2,;-3,;15,;-200,\dots
$$

even though the actual heat equation is perfectly smooth.

That is numerical instability.

---

## 9. CFL condition

For transport problems, stability is often related to the **Courant-Friedrichs-Lewy condition**.

Consider:

$$
u_t + c u_x = 0
$$
The physical wave moves during one timestep by:

$$
c\Delta t
$$

The grid spacing is:

$$
\Delta x
$$
Define the Courant number:

$$
C=\frac{c\Delta t}{\Delta x}
$$

The intuition is extremely useful:

> During one timestep, how many grid cells does information travel?

For many explicit methods, we require approximately:

$$
\boxed{C\lesssim1}
$$

meaning:

$$
c\Delta t\lesssim\Delta x
$$
Why?

Because the numerical algorithm communicates information only between nearby grid cells.

If the physical disturbance jumps across several cells in one timestep, the discretization cannot represent causality correctly.

So the CFL condition can be thought of as:

$$
\boxed{ \text{numerical information propagation must keep up with physical information propagation} }
$$

---

## 10. CFL is method-dependent

It's important not to memorize:

$$
C<1
$$

as a universal law.

The actual condition depends on:

* PDE,
* spatial discretization,
* time integrator,
* number of dimensions,
* mesh geometry.

For diffusion:

$$
\Delta t \propto \Delta x^2
$$

For advection:

$$
\Delta t \propto \Delta x
$$
This has major computational consequences.

If you halve the grid spacing for an explicit diffusion solver:

$$
\Delta x\rightarrow\frac{\Delta x}{2},
$$

then stable timestep often needs to become:

$$
\Delta t\rightarrow\frac{\Delta t}{4}
$$

You've increased spatial resolution and simultaneously increased the number of time steps.

This can become very expensive.

---

## 11. Implicit methods

One solution is to use an implicit time integrator.

Instead of:

$$
u^{n+1}=u^n+\Delta tF(u^n),
$$

use something like:

$$
u^{n+1} = u^n+\Delta tF(u^{n+1})
$$
Now the new state appears on both sides.

Therefore each timestep requires solving an algebraic system:

$$
A u^{n+1}=b
$$

Implicit schemes often have much better stability properties.

But there is an important distinction:

$$
\boxed{\text{stable} \neq \text{accurate}}
$$

A method may permit a gigantic timestep without blowing up, while still producing a terrible approximation.

---

## 12. Stability vs accuracy

Suppose a transient physical phenomenon changes on a characteristic timescale:

$$
\tau=0.01\text{ s}
$$
Your implicit solver might remain stable with:

$$
\Delta t=1\text{ s}
$$

But then you're skipping over the physical phenomenon you care about.

So you need:

$$
\text{stability constraint}
$$

and separately:

$$
\text{accuracy constraint}
$$
A stable simulation is merely one that doesn't numerically explode.

It isn't automatically correct.

---

## 13. Convergence: the big mathematical idea

A numerical scheme is convergent if:

$$
u_{h,\Delta t}\rightarrow u
$$

as:

$$
h,\Delta t\rightarrow0
$$

For linear initial-value problems, there is a famous principle:

$$
\boxed{ \text{consistency}+\text{stability} \Rightarrow \text{convergence} }
$$

under appropriate assumptions.

This is the spirit of the **Lax equivalence theorem**.

Intuitively:

* consistency says you're approximating the correct PDE,
* stability says errors don't blow up,
* therefore refinement should take you toward the true solution.

---

## 14. Residuals: how well does the numerical solution satisfy the equations?

Suppose the discretized equations are:

$$
A\mathbf u=\mathbf b
$$
$$
After an iterative solver produces (\hat{\mathbf u}), calculate:
$$

$$
\mathbf r = \mathbf b-A\hat{\mathbf u}
$$

This is the **residual**.

If $\mathbf r=0,$. the discrete equations are satisfied exactly.

In practice we check:

$$
|\mathbf r| < \epsilon
$$
For nonlinear systems:

$$
F(\mathbf u)=0,
$$

the residual is simply:

$$
\mathbf r=F(\mathbf u)
$$

---

## 15. Small residual does NOT imply correct PDE solution

This is one of the most important lessons in numerical simulation.

Suppose you discretize the PDE on a terrible grid.

Then you solve:

$$
A_h\mathbf u_h=b_h
$$

to machine precision.

You might have:

$$
|A_h\mathbf u_h-b_h|=10^{-12}
$$
Fantastic residual.

But (\mathbf u_h) may still be a poor approximation to the continuous PDE solution.

Why?

Because the residual tells you:

> “Did I solve the discrete equations?”

It does not tell you:

> “Were the discrete equations a sufficiently accurate representation of the continuous PDE?”

Therefore:

$$
\boxed{ \text{solver convergence} \neq \text{mesh convergence} }
$$

This distinction is critical.

---

## 16. Three different meanings of “convergence”

Simulation software often uses the word **converged** ambiguously.

You should separate:

### Iterative convergence

Did the numerical algebra solver satisfy

$$
A\mathbf u\approx b?
$$

### Temporal convergence

Does decreasing \Delta t  stop changing the result?

### Spatial convergence

Does decreasing h  stop changing the result?

A CFD solver saying:

> CONVERGED

usually primarily refers to iterative residual convergence.

That alone is not sufficient evidence of physical accuracy.

---

## 17. Conservation error

Now let's return to your earlier intuition about conservation laws.

Suppose mass conservation requires:

$$
\frac{d}{dt} \int_\Omega \rho,dV = * \int_{\partial\Omega} \rho\mathbf u\cdot\mathbf n,dS.
$$

If the domain has one inlet and one outlet and the system is steady, we expect:

$$
\dot m_{\text{in}} \approx \dot m_{\text{out}}
$$

We can measure:

$$
\epsilon_m = \frac{ |\dot m_{\text{in}}-\dot m_{\text{out}}| }{ \dot m_{\text{in}} }.
$$

If:

$$
\dot m_{\text{in}}=10.0\text{ kg/s},
$$

and:

$$
\dot m_{\text{out}}=9.9998\text{ kg/s},
$$

then conservation looks excellent.

If:

$$
\dot m_{\text{out}}=8.2\text{ kg/s},
$$

there is clearly a problem.

Possible causes:

* solver hasn't converged,
* boundary conditions are inconsistent,
* discretization is wrong,
* mesh quality is bad,
* implementation bug exists.

---

## 18. Conservation can be checked globally and locally

There are two useful checks.

### Global conservation

Across the entire simulation:

$$
\text{total inflow} - \text{total outflow} + \text{generation} \approx \text{accumulation}.
$$

### Local conservation

For every numerical cell:

$$
\text{cell inflow} - \text{cell outflow} + \text{source} \approx \frac{d}{dt}\text{cell content}.
$$

Finite-volume methods are especially attractive because local conservation is built naturally into the discretization.

---

## 19. Conservation does not guarantee accuracy either

Here's another subtle point.

You could construct a numerical solution that conserves mass perfectly but has the wrong velocity profile.

For example, suppose the correct pipe flow is:

$$
u(r)
$$

with a parabolic profile.

A bad numerical solution might give the wrong profile but maintain exactly the same total mass flux:

$$
\int_A \rho u,dA
$$
So:

$$
\boxed{\text{conservation is necessary in many physical problems, but not sufficient}}
$$

You want all of these together:

$$
\text{conservation} + \text{residual convergence} + \text{mesh convergence} + \text{time convergence} + \text{physical validation}.
$$

---

## 20. Benchmark problems

One of the best ways to verify a solver is to use a problem where the answer is known.

For example, suppose:

$$
-u''=\pi^2\sin(\pi x),
$$

with:

$$
u(0)=u(1)=0
$$

The exact solution is:

$$
u(x)=\sin(\pi x)
$$
Now calculate the numerical error:

$$
e_h = u-u_h
$$

Measure:

$$
|e_h|_{L^2}
$$
Then refine:

$$
h,\frac h2,\frac h4,\dots
$$

and verify:

$$
|e_h| \propto h^p
$$

This is extremely powerful because you're testing the whole numerical pipeline.

---

## 21. Method of manufactured solutions

But what if your real PDE has no analytical solution?

A very clever technique is the **Method of Manufactured Solutions (MMS)**.

Instead of starting with the PDE and trying to solve it, choose a solution yourself.

For example:

$$
u(x,y)=\sin(\pi x)\cos(\pi y)
$$
Now compute what source term would make this satisfy your PDE.

Suppose:

$$
-\nabla^2u=f
$$

Calculate:

$$
f=-\nabla^2u
$$
Now you know the exact solution because you deliberately manufactured it.

Then run your numerical solver against that problem and see whether it recovers:

$$
u(x,y)
$$

This is one of the strongest tools for verifying a PDE code implementation.

---

## 22. Verification vs validation

This distinction deserves its own section.

## Verification

Question:

> Are we solving our mathematical model correctly?

Includes:

* code verification,
* manufactured solutions,
* benchmark solutions,
* mesh refinement,
* timestep refinement,
* residual convergence,
* observed convergence order.

Symbolically:

$$
\boxed{ \text{PDE} \xrightarrow[\text{numerics}]{} \text{correct numerical approximation?} }
$$

## Validation

Question:

> Does the mathematical model accurately represent the physical world?

Compare against:

* experimental measurements,
* laboratory tests,
* observational data,
* trusted physical correlations.

Symbolically:

$$
\boxed{ \text{simulation} \leftrightarrow \text{reality} }
$$

A solver can be perfectly verified but still fail validation because the physics model is incomplete.

---

## 23. Example: heat conduction

Suppose your solver perfectly solves:

$$
\rho c_pT_t = k\nabla^2T
$$
Mesh convergence is excellent.

Residual:

$$
10^{-10}
$$

Energy conservation:

$$
99.9999%
$$
But experimental temperature is still substantially different.

Maybe the numerical solver isn't the problem.

Maybe your model ignored:

* radiation,
* convection,
* temperature-dependent (k),
* contact resistance,
* phase change.

This is **model-form error**.

No amount of mesh refinement fixes missing physics.

---

## 24. Boundary conditions can dominate the result

This is another practical issue.

Suppose your PDE solution is mathematically perfect, but you assumed:

$$
T_{\text{wall}}=300K
$$

Actual wall temperature is:

$$
340K
$$
The simulation may be numerically flawless and physically useless.

For many engineering simulations, uncertainty in:

* boundary conditions,
* material parameters,
* geometry,

can exceed discretization error.

So ultimately you want to think about:

$$
\boxed{ \text{numerical error} + \text{model error} + \text{parameter uncertainty} }
$$

---

## 25. Mesh quality matters

In 2D/3D simulations, mesh spacing isn't the whole story.

Bad elements can introduce numerical problems.

For finite elements, you might worry about:

* highly skewed elements,
* extreme aspect ratios,
* poor angles,
* distorted cells.

For CFD:

* skewness,
* orthogonality,
* aspect ratio,
* wall-normal resolution.

A mesh can contain millions of cells and still be poor.

More cells does not automatically mean better simulation.

---

## 26. Adaptive mesh refinement

Uniformly refining everything can be wasteful.

Suppose the solution is smooth here:

```text

-------------------------------

```

but changes sharply near:

```text
 |

------------------|████
 |
```

You should place more cells where the solution requires them.

This gives **adaptive mesh refinement (AMR)**:

```text
coarse mesh

|----|----|----|----|

adaptive

|----|----|-|-|||||||----|
```

The solver may refine regions with:

* large gradients,
* large estimated errors,
* shocks,
* boundary layers,
* complex interfaces.

This is a very important concept for efficient PDE computation.

---

## 27. Boundary-layer example

Consider high-Reynolds-number fluid flow over a wall.

Away from the wall, velocity changes slowly.

Near the wall:

$$
\frac{\partial u}{\partial y}
$$

can be huge.

Using the same mesh spacing everywhere would either:

1. fail to resolve the wall layer, or 2. require an enormous number of cells.

So practical CFD meshes often look roughly like:

```text
fluid
|
| large cells
|
|--------------------

|- - - - - - - - - -
|--------------------

||||||||||||||||||||| very thin cells
==================== wall
```

Mesh resolution must follow the physics.

---

## 28. Discontinuities and shocks complicate convergence

Everything becomes harder when the solution isn't smooth.

For example:

$$
u_t + f(u)_x=0
$$

can produce shocks.

At a shock:

$$
u(x)
$$

may be discontinuous.

Classical Taylor-series error arguments break down.

Higher-order numerical methods may create oscillations:

```text
true shock:

─────────|
 |
 |────────

bad numerical result:

──────/\/\/\/\────
```

This is related to phenomena such as Gibbs oscillations.

Then specialized methods are used:

* upwinding,
* flux limiters,
* TVD schemes,
* WENO,
* Riemann solvers.

This is why “higher order” does not automatically mean “better everywhere”.

---

## 29. Numerical diffusion

Suppose the actual advection equation transports a sharp blob:

```text
initial:

-----████-----

exact later:

---------████-
```

A low-order numerical scheme might produce:

```text

-------░▒██▒░-
```

The solution became artificially smeared.

That's **numerical diffusion**.

The physical PDE didn't contain that much diffusion.

The discretization introduced it.

This is a classic example of a simulation being:

* stable,
* converged,
* conservative,

yet still quantitatively inaccurate.

---

## 30. Numerical dispersion

For waves, instead of excessive smoothing, different wavelengths may travel at the wrong speeds.

That's **numerical dispersion**.

Suppose the actual wave is:

$$
u(x,t)=\sin(kx-\omega t)
$$

The discrete numerical method may effectively produce:

$$
\omega_h(k) \neq \omega(k)
$$
So the numerical wave's phase drifts.

This is particularly important for:

* acoustics,
* electromagnetics,
* seismic waves,
* wave propagation.

Mesh resolution must often be expressed as:

$$
\text{points per wavelength}
$$

---

## 31. A practical hierarchy of trust

When reviewing a numerical PDE simulation, I'd ask questions in roughly this order.

### 1. Is the mathematical model appropriate?

Are the correct PDEs and constitutive laws being used?

### 2. Are initial and boundary conditions physically correct?

### 3. Is the discretization appropriate?

FEM? FVM? finite difference? order?

### 4. Is the mesh adequate?

Especially in high-gradient regions.

### 5. Is the timestep adequate?

Not just stable—accurate.

### 6. Did the iterative solver converge?

Check residuals.

### 7. Are conserved quantities balanced?

Mass, energy, momentum, charge.

### 8. Is the solution mesh-independent?

Refinement study.

### 9. Is it timestep-independent?

Time refinement study.

### 10. Does it reproduce analytical/benchmark problems?

Verification.

### 11. Does it match experimental observations?

Validation.

That's a much stronger standard than:

> solver says “converged”.

---

## 32. One very useful example

Suppose we simulate heat diffusion and measure maximum temperature.

### Mesh study

$$
h=0.1: \qquad T_{\max}=423.7 K
$$

$$
h=0.05: \qquad T_{\max}=418.1 K
$$

$$
h=0.025: \qquad T_{\max}=416.8 K
$$

$$
h=0.0125: \qquad T_{\max}=416.5 K
$$

Looks promising.

Then do timestep study:

$$
\Delta t=1: 416.5K
$$

$$
\Delta t=0.5: 416.2K
$$

$$
\Delta t=0.25: 416.1K
$$

So perhaps:

$$
T_{\max}\approx416K
$$
Now check energy balance:

E_{\text{in}} -
## E_{\text{out}}
\Delta E_{\text{stored}}
\approx0.

Then compare to experimental measurement:

$$
T_{\max}^{\text{experiment}} = 418\pm3K
$$

Now you have a much stronger case that the simulation is meaningful.

---

## 33. The fundamental distinction

It helps to separate three questions:

$$
\boxed{ \begin{array}{ll} \textbf{Algebraic convergence:} & \text{Did I solve the discrete equations?}[1mm] \textbf{Numerical convergence:} & \text{Do the discrete equations approach the PDE solution?}[1mm] \textbf{Physical validation:} & \text{Does the PDE solution describe reality?} \end{array} }
$$

These are independent.

You can succeed at one and fail at another.

---

## 34. Connecting this back to AI/PDE models

This becomes particularly important when we move into PINNs or neural operators.

Suppose a PINN predicts:

$$
u_\theta(x,t)
$$
We might calculate the PDE residual:

$$
r_\theta = u_t-\alpha u_{xx}
$$

And get:

$$
|r_\theta|\approx10^{-5}
$$
It is tempting to say:

> the neural network solved the PDE.

But, exactly as with classical numerical methods:

$$
\boxed{\text{small residual does not automatically imply small solution error}}
$$

You still care about:

* boundary-condition error,
* initial-condition error,
* conservation error,
* generalization,
* resolution of sharp features,
* comparison against reference solvers,
* physical validation.

This is one of the most important bridges between classical numerical PDEs and Physics-AI.

---

## 35. The mental model I would retain

Think of numerical PDE trustworthiness as layers:

$$
\boxed{ \begin{array}{c} \text{Physical model correct?}\\ \downarrow\\ \text{BCs/ICs/material data correct?}\\ \downarrow\\ \text{Discretization consistent?}\\ \downarrow\\ \text{Scheme stable?}\\ \downarrow\\ \text{Linear/nonlinear solver converged?}\\ \downarrow\\ \text{Mesh/time refinement converged?}\\ \downarrow\\ \text{Conservation satisfied?}\\ \downarrow\\ \text{Benchmarks reproduced?}\\ \downarrow\\ \text{Experimental validation?} \end{array}}
$$

Only at the bottom should you start saying:

> “I trust this simulation.”
