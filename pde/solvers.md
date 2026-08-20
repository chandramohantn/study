Yes. In fact, **most practical PDE work is done exactly this way**: you formulate the physical problem, discretize it, and let a numerical PDE solver compute an approximate solution.

There is one important correction to the mental model, though:

$$
\boxed{ \text{You usually don't give a solver "physics constraints" as arbitrary text.} }
$$

You express the physics mathematically—as governing PDEs, constitutive equations, algebraic constraints, source terms, initial conditions, and boundary conditions. The solver then solves that resulting mathematical system.

Modern tools range from general PDE frameworks such as **FEniCSx** and MATLAB PDE Toolbox to domain-specific solvers such as **OpenFOAM** for CFD and multiphysics environments such as **COMSOL**. FEniCSx exposes finite-element variational forms and explicit boundary-condition objects; MATLAB supports stationary, time-dependent, nonlinear, and eigenvalue PDE problems; COMSOL exposes general/coefficient/weak-form PDE interfaces and constraint boundary conditions. ([FEniCS Project][1])

---

## 1. What you actually provide to a PDE solver

A typical PDE problem looks approximately like:

$$
\boxed{ \begin{aligned} \text{Geometry} \\ +~\text{PDE(s)} \\ +~\text{material properties} \\ +~\text{initial conditions} \\ +~\text{boundary conditions} \\ +~\text{physical/algebraic constraints} \\ +~\text{numerical settings} \end{aligned}}
$$

and the solver gives you an approximation of $u(x,y,z,t)$ For example:

```text
Problem definition
 │
 ├── Geometry
 │ └── 1 m × 1 m plate
 │
 ├── PDE
 │ └── ∂T/∂t = α∇²T
 │
 ├── Initial condition
 │ └── T(x,y,0) = 20°C
 │
 ├── Boundary conditions
 │ ├── left wall = 100°C
 │ ├── right wall = 20°C
 │ └── top/bottom insulated
 │
 ├── Material
 │ └── α = 1.2×10⁻⁵ m²/s
 │
 └── Solve
 ↓
 T(x,y,t)
```

That is essentially how commercial simulation packages operate.

---

## 2. Let's construct a concrete problem

Suppose we have a metal rod:

$$
0\leq x\leq1
$$
We want to determine its temperature.

The governing PDE is

$$
\frac{\partial T}{\partial t} = \alpha \frac{\partial^2T}{\partial x^2}
$$

But that alone isn't enough.

---

## Input 1 — Governing PDE

You tell the solver:

$$
T_t-\alpha T_{xx}=0
$$
This represents heat diffusion.

---

## Input 2 — Material property

Suppose

$$
\alpha=10^{-4}\text{ m}^2/\text{s}
$$

The solver needs this because different materials diffuse heat at different rates.

---

## 3. Initial condition

You have to tell the solver:

> What did the system look like at (t=0)?

For example:

$$
T(x,0)=20^\circ C
$$
Meaning the whole rod starts at room temperature.

Graphically:

```text
T

20 ─────────────────────────
 0 1 x
```

Or the initial condition could be spatially varying:

$$
T(x,0) = 20+80e^{-100(x-0.5)^2}
$$

Something like:

```text
temperature

100 /\
 / \
 / \
20 ──────────/──────\─────────
 0 0.5 1
```

A PDE solver represents this as an initial **field**.

MATLAB's PDE functionality, for example, exposes explicit initial-condition APIs and supports different initial values for components of systems of PDEs. ([MathWorks][2])

---

## 4. Boundary condition: Dirichlet

Now suppose we hold the left side at (100^\circ C):

$$
T(0,t)=100
$$
And the right side at (20^\circ C):

$$
T(1,t)=20
$$

These are **Dirichlet boundary conditions**.

They specify the value of the unknown directly.

Conceptually:

```text
100°C 20°C
 │ │
 ▼ ▼

 ●=========================================●
 x=0 x=1
```

The solver is being told:

> Whatever solution you find, these points must always have these temperatures.

Packages explicitly associate these conditions with geometric boundaries. FEniCSx, for example, provides Dirichlet boundary-condition objects; MATLAB similarly lets you attach conditions to identified edges or faces. ([FEniCS Project][3])

---

## 5. Boundary condition: Neumann

Instead, suppose the right side is insulated.

Physically:

$$
\text{no heat leaves}
$$
Heat flux is

$$
q=-k\frac{\partial T}{\partial x}
$$

No heat flux means $q=0,$. so

$$
\frac{\partial T}{\partial x}=0
$$

This is a **Neumann boundary condition**.

You are not specifying temperature.

You are specifying its derivative:

$$
\boxed{ \frac{\partial T}{\partial n}=0 }
$$

where $n$ is normal to the surface.

Conceptually:

```text
 insulated wall
 │
 │
===========>│
 heat │ X no heat transfer
 │
```

COMSOL's general PDE formulation, for example, explicitly includes generalized Neumann boundary conditions alongside constraint/Dirichlet conditions. ([COMSOL Documentation][4])

---

## 6. Boundary condition: Robin

There's also a very common mixed condition.

Suppose heat escapes into surrounding air.

Newton's cooling law says

$$
-k\frac{\partial T}{\partial n} = h(T-T_{\infty})
$$
Here

* k = thermal conductivity,
* h = convective heat-transfer coefficient,
* (T_\infty) = ambient temperature.

This combines the field and its derivative.

It is often called a **Robin** or mixed boundary condition.

So the three important types are:

| Type | Form | Physical interpretation |
| --------- | ----------------------------- | ----------------------- |
| Dirichlet | (u=g) | specify value |
| Neumann | (\partial u/\partial n=g) | specify flux |
| Robin | (au+b\partial u/\partial n=g) | mixed relationship |

---

## 7. What about a "physical constraint"?

Now we get to your previous question.

Suppose we are modeling incompressible water.

A physical statement is:

> water is approximately incompressible.

Mathematically that means:

$$
\boxed{\nabla\cdot\mathbf u=0}
$$

This becomes another equation the solver must satisfy.

For Navier-Stokes:

$$
\rho \left( \frac{\partial\mathbf u}{\partial t} + (\mathbf u\cdot\nabla)\mathbf u \right) = -\nabla p + \mu\nabla^2\mathbf u
$$

$$
plus \nabla\cdot\mathbf u=0. So now our unknowns are u_x,\quad u_y,\quad u_z,\quad p And the solver simultaneously tries to find fields satisfying both:
$$
$$
\text{momentum conservation}
$$

and $\text{mass conservation}$ That's an example of a physical constraint becoming an additional PDE.

---

## 8. Another constraint example: rigid wall

Suppose fluid flows through a pipe.

At the wall:

$$
\mathbf u=0
$$
Why?

Because of the **no-slip condition**.

Graphically:

```text
wall ───────────────────────────

u = 0 → →→ →→→

 fluid

u = 0 → →→ →→→

wall ───────────────────────────
```

At the surface, u_x=u_y=u_z=0. That's a physical assumption expressed as a boundary condition.

---

## 9. Another physical constraint: symmetry

Suppose your geometry is symmetric:

```text
 symmetric object

 ┌───────────┐
 │ │
 │ │

-------│-----------│------- symmetry axis
 │ │
 │ │
 └───────────┘
```

Instead of simulating everything, you might simulate only half.

On the symmetry boundary you impose something like

$$
\frac{\partial T}{\partial n}=0
$$

That means there is no heat flow across the symmetry plane.

OpenFOAM, for example, distinguishes ordinary value/gradient boundary conditions from geometric constraints including symmetry and cyclic conditions. ([OpenFOAM][5])

---

## 10. Let's look at an entire CFD problem

Suppose you want airflow through a pipe.

Your domain:

```text
 pipe

 inlet outlet
 │ │
 ↓ ↓

 ┌───────────────────────────────┐
 → │ │ →
 → │ │ →
 → │ │ →
 └───────────────────────────────┘
 walls
```

### Governing equations

Momentum:

$$
\rho\left( u_t+(\mathbf u\cdot\nabla)\mathbf u \right) = -\nabla p+\mu\nabla^2\mathbf u.
$$

Mass conservation:

$$
\nabla\cdot\mathbf u=0
$$
### Initial conditions

Perhaps:

$$
\mathbf u(x,0)=0
$$

The fluid initially isn't moving.

### Inlet BC

Specify velocity:

$$
\mathbf u=(1,0,0)\text{ m/s}
$$
### Wall BC

No slip:

$$
\mathbf u=0
$$

### Outlet BC

Perhaps:

$$
p=0
$$

in gauge pressure.

The CFD solver now computes $\mathbf u(x,y,z,t) $ and $p(x,y,z,t)$ That is broadly the workflow of CFD tools such as OpenFOAM. OpenFOAM emphasizes that boundary conditions are a critical part of case specification, and inappropriate combinations can produce physically incorrect results or solver failure. ([OpenFOAM Documentation][6])

---

## 11. What does this look like in actual software?

There are two broad styles.

## Style A — physics GUI

Something such as COMSOL might conceptually look like:

```text
Geometry
 └── Rectangle

Material
 └── Steel
 density =...
 conductivity =...
 heat capacity =...

Physics
 └── Heat Transfer
 ├── Initial Values
 │ T = 293.15 K
 │
 ├── Left Boundary
 │ Temperature = 373.15 K
 │
 ├── Right Boundary
 │ Temperature = 293.15 K
 │
 └── Top / Bottom
 Thermal Insulation

Mesh
 └── Fine

Study
 └── Time Dependent
 0 → 100 seconds

Solve
```

COMSOL also provides equation-based interfaces where you explicitly enter coefficient-form, general-form, or weak-form PDEs rather than choosing a predefined physics module. ([COMSOL Documentation][4])

---

## 12. Style B — code-based PDE framework

Something such as FEniCSx takes a more mathematical approach.

Consider Poisson's equation:

$$
-\nabla^2u=f
$$
With:

$$
u=0
$$

on part of the boundary.

You typically write a **variational/weak formulation** instead of directly handing the software the symbolic string

```text
-∇²u = f
```

Conceptually:

```python
mesh = create_mesh(...)

V = create_function_space(mesh)

u = TrialFunction(V)
v = TestFunction(V)

a = dot(grad(u), grad(v)) * dx
L = f * v * dx

bc = DirichletBC(value=0, boundary=...)

solve(a == L, u, bc)
```

The official DOLFINx Poisson example uses exactly this finite-element pattern: a domain, Dirichlet/Neumann portions of the boundary, a source (f), and bilinear/linear variational forms. ([FEniCS Project][7])

This is an important concept we'll eventually want to unpack:

$$
\boxed{ \text{PDE} \rightarrow \text{weak form} \rightarrow \text{mesh} \rightarrow \text{matrix equations} \rightarrow \text{numerical solution} }
$$

---

## 13. What the solver actually does internally

Suppose your PDE is continuous:

$$
-\nabla^2u=f
$$

The solver creates a mesh:

```text
Continuous domain

┌─────────────────────┐
│ │
│ │
│ │
└─────────────────────┘

 ↓

Finite mesh

●────●────●────●
│ \ │ \ │ \ │
│ \ │ \ │ \ │
●────●────●────●
│ \ │ \ │ \ │
│ \ │ \ │ \ │
●────●────●────●
```

Instead of finding infinitely many values $u(x,y), $ it finds a finite vector:

$$
\mathbf U= \begin{bmatrix} u_1\ u_2\ \vdots\ u_N \end{bmatrix}
$$

Eventually your PDE becomes something like $A\mathbf U=\mathbf b$. For nonlinear problems:

$$
F(\mathbf U)=0
$$

For transient PDEs:

$$
M\frac{d\mathbf U}{dt} + F(\mathbf U)=0
$$
At that point numerical linear algebra takes over.

---

## 14. Your conservation-law intuition appears again here

Suppose we solve fluid flow.

We could get candidate velocity fields such as:

$$
\mathbf u_1,\mathbf u_2,\mathbf u_3,\dots
$$

But incompressibility requires \nabla\cdot\mathbf u=0. The solver is not usually doing:

```text
solve momentum equation
 ↓
get 10,000 answers
 ↓
test incompressibility
 ↓
discard 9,999
```

Instead it constructs a coupled system:

$$
\begin{cases} \text{momentum equation}=0\\ \nabla\cdot\mathbf u=0 \end{cases}
$$

and solves them simultaneously:

```text
Momentum conservation ─┐
 │
Mass conservation ─────┤
 │
Boundary conditions ───┤
 ├── numerical system ──→ solution
Initial conditions ────┤
 │
Material relations ────┘
```

That distinction is important.

---

## 15. Not all constraints have the same role

I'd classify the information given to a PDE solver like this:

$$
\boxed{ \begin{array}{lll} \textbf{Governing laws} && \text{What equations hold?}[2mm] \textbf{Constitutive laws} && \text{How does the material behave?}[2mm] \textbf{Initial conditions} && \text{Where does the system start?}[2mm] \textbf{Boundary conditions} && \text{How does it interact with surroundings?}[2mm] \textbf{Constraints} && \text{What states are physically permissible?} \end{array}}
$$

For example, for an incompressible Newtonian fluid:

### Governing law

Newton's second law / momentum conservation:

$$
\rho\frac{D\mathbf u}{Dt} = -\nabla p+\nabla\cdot\boldsymbol\tau
$$

### Constitutive law

Newtonian viscosity:

$$
\boldsymbol\tau = \mu \left( \nabla\mathbf u+\nabla\mathbf u^T \right).
$$

### Constraint

Incompressibility:

$$
\nabla\cdot\mathbf u=0
$$
### Initial condition \mathbf u(x,0)=\mathbf u_0(x). ### Boundary conditions
$$
\mathbf u=\mathbf u_{\text{inlet}}
$$

at the inlet, $\mathbf u=0$. on walls,

and some appropriate outlet pressure/traction condition.

Put all of that together and you finally have a well-defined **initial-boundary-value problem**.

---

## 16. So what PDE solver would I use?

For someone coming from Python/ML, I'd separate them this way.

| Tool | Best mental model |
| ----------------------- | ------------------------------------------------------ |
| **FEniCSx** | General-purpose programmable finite-element framework |
| **COMSOL** | General multiphysics modeling environment |
| **OpenFOAM** | CFD-focused simulation framework |
| **MATLAB PDE Toolbox** | Engineering-oriented finite-element PDE environment |
| **ANSYS** | Industrial structural/thermal/CFD simulation ecosystem |
| **deal.II / Firedrake** | Advanced programmable finite-element frameworks |

For learning, **FEniCSx is especially useful** because it forces you to understand the mathematics rather than hiding everything behind a GUI. DOLFINx is the current computational environment of the FEniCSx project and exposes its problem-solving interface in Python and C++. ([GitHub][8])

---

## The important conceptual shift

Your original model was roughly:

$$
\text{PDE} + \text{extra information} \rightarrow \text{solver} \rightarrow \text{answer}.
$$

$$
I'd refine it to:
$$

$$
\boxed{ \begin{array}{c} \text{Physical system}\\ \downarrow\\ \text{Conservation laws + constitutive laws}\\ \downarrow\\ \text{PDEs}\\ +\\ \text{Initial conditions}\\ +\\ \text{Boundary conditions}\\ +\\ \text{constraints}\\ \downarrow\\ \text{well-posed mathematical problem}\\ \downarrow\\ \text{discretization}\\ \downarrow\\ \text{numerical solver}\\ \downarrow\\ u(x,y,z,t) \end{array} }
$$

And this leads naturally to what I think is the **most important next question**: how does a solver turn something continuous like $-\nabla^2u=f$. into the finite matrix equation

$$
A\mathbf u=\mathbf b?
$$

If we understand that using a tiny 1D heat/Poisson example, finite differences, finite elements, meshes, numerical approximation, and eventually why Physics-ML models can replace parts of these solvers will all become much easier.

The next useful step is to understand how a continuous PDE becomes something a computer can actually solve.

Take a simple 1D Poisson equation:

$$
-\frac{d^2u}{dx^2}=f(x), \qquad x\in[0,1]
$$

with boundary conditions $u(0)=0,\qquad u(1)=0$. The PDE describes infinitely many points in the interval. A computer cannot store infinitely many values, so we **discretize the domain**.

Suppose we choose grid points:

$$
x_0, x_1, x_2, \dots, x_N
$$
For simplicity, use equal spacing:

$$
h = \frac{1}{N}
$$

Then we only solve for $u_i \approx u(x_i)$ So the continuous function $u(x) $ becomes a finite vector:

$$
\mathbf u = \begin{bmatrix} u_0\ u_1\ \vdots\ u_N \end{bmatrix}
$$

That is the first major transition:

$$
\boxed{\text{continuous field} \rightarrow \text{finite set of unknowns}}
$$

## 1. Approximating derivatives numerically

The key question is now:

> How do we represent (\frac{d^2u}{dx^2}) using values at grid points?

For a sufficiently smooth function, the second derivative at point (x_i) can be approximated as

$$
\frac{d^2u}{dx^2}(x_i) \approx \frac{u_{i-1}-2u_i+u_{i+1}}{h^2}
$$
This is the familiar finite-difference approximation.

So the PDE

$$
-u''(x)=f(x)
$$

becomes, at every interior grid point,

$$
-\frac{u_{i-1}-2u_i+u_{i+1}}{h^2} = f_i
$$
$$
Multiply through by (h^2):
$$

$$
-u_{i-1}+2u_i-u_{i+1}=h^2f_i
$$
Now the PDE has become an ordinary algebraic equation.

Do this at every grid point and you get a system of equations.

---

## 2. A tiny concrete example

Suppose we choose five grid points:
$$
x_0=0,\quad x_1=0.25,\quad x_2=0.5,\quad x_3=0.75,\quad x_4=1
$$
So:

$$
h=0.25
$$

The boundary conditions tell us:

$$
u_0=0, \qquad u_4=0
$$
The only unknowns are:

$$
u_1,u_2,u_3
$$
$$
At (x_1):
$$

$$
-u_0+2u_1-u_2=h^2 f_1
$$
$$
Since (u_0=0):
$$

$$
2u_1-u_2=h^2f_1
$$
$$
At (x_2):
$$

$$
-u_1+2u_2-u_3=h^2f_2
$$
$$
At (x_3):
$$

$$
-u_2+2u_3-u_4=h^2f_3
$$
$$
Since (u_4=0):
$$

$$
-u_2+2u_3=h^2f_3
$$
Now write them as a matrix:
$$
\begin{bmatrix} 2 & -1 & 0\ -1 & 2 & -1\ 0 & -1 & 2 \end{bmatrix} \begin{bmatrix} u_1\ u_2\ u_3 \end{bmatrix} = h^2 \begin{bmatrix} f_1\ f_2\ f_3 \end{bmatrix}
$$
This is:

$$
\boxed{A\mathbf u=\mathbf b}
$$

Now the problem is no longer "solve a PDE".

It is:

> solve a linear algebra system.

That is what the numerical PDE solver actually does.

---

## 3. Why the matrix has this pattern

Look at the matrix:
$$
A= \begin{bmatrix} 2 & -1 & 0\ -1 & 2 & -1\ 0 & -1 & 2 \end{bmatrix}
$$
Each equation couples a point to its immediate neighbors.

That's exactly what the second derivative was doing physically:

$$
u_{i-1}-2u_i+u_{i+1}
$$

So the matrix structure reflects local spatial interactions.

For a 2D PDE, each point gets coupled to its neighbors in two directions.

For example, the 2D Laplacian:

$$
\nabla^2u = u_{xx}+u_{yy}
$$

becomes approximately

$$
\frac{ u_{i+1,j} + u_{i-1,j} + u_{i,j+1} + u_{i,j-1} - 4u_{i,j} }{h^2}
$$

So each grid cell is coupled to its four neighbors:

```text
 u(i,j+1)
 |
u(i-1,j) -- u(i,j) -- u(i+1,j)
 |
 u(i,j-1)
```

This produces a large sparse matrix.

---

## 4. Boundary conditions modify the algebraic system

This is where your earlier question becomes concrete.

Suppose the left boundary is $u(0)=5$. Then the first interior equation becomes $-u_0+2u_1-u_2=h^2f_1$. Since $u_0=5,$. we get $2u_1-u_2 = h^2f_1+5$. So the boundary condition changes the right-hand side of the linear system.

A Neumann condition behaves differently.

Suppose:

$$
u'(0)=0
$$
Using a finite difference:

$$
\frac{u_1-u_0}{h}=0
$$

Therefore:

$$
u_1=u_0
$$
That relation is inserted into the algebraic system.

So boundary conditions directly change the equations the solver constructs.

---

## 5. What happens with a time-dependent PDE?

Now consider the heat equation:

$$
\frac{\partial u}{\partial t} = \alpha\frac{\partial^2u}{\partial x^2}
$$

We discretize space exactly as before:

$$
\frac{\partial u_i}{\partial t} = \alpha \frac{u_{i-1}-2u_i+u_{i+1}}{h^2}
$$
Notice something interesting.

We discretized **space**, but not time.

So instead of one PDE, we now have a system of ODEs:

$$
\frac{d\mathbf u}{dt} = A\mathbf u
$$

This is called the **method of lines**.

Then we use an ODE time integrator.

For example, forward Euler:

$$
u_i^{n+1} = u_i^n + \Delta t \alpha \frac{ u_{i-1}^n-2u_i^n+u_{i+1}^n }{h^2}.
$$

This means:

$$
\boxed{\text{next temperature} = \text{current temperature} + \text{small change}}
$$

at every time step.

---

## 6. Initial conditions become the starting vector

For the heat equation, suppose $u(x,0)=g(x)$. On the grid:

$$
u_i^0=g(x_i)
$$

So the initial condition simply becomes:

$$
\mathbf u(0)= \begin{bmatrix} g(x_1)\ g(x_2)\ \vdots \end{bmatrix}
$$

Then the solver advances:

$$
\mathbf u^0 \rightarrow \mathbf u^1 \rightarrow \mathbf u^2 \rightarrow \cdots
$$

through time.

So the roles are now very concrete:

$$
\boxed{ \begin{aligned} \text{PDE} &\rightarrow \text{equations}\ \text{boundary conditions} &\rightarrow \text{spatial constraints}\ \text{initial conditions} &\rightarrow \text{starting state}\ \text{solver} &\rightarrow \text{numerical trajectory} \end{aligned} }
$$

---

## 7. Where conservation enters numerically

This is where things become subtle.

The original continuous PDE may conserve something exactly.

For example, an isolated heat system conserves total energy.

But after discretization, your numerical method may or may not conserve it exactly.

A poorly chosen discretization can introduce:

* artificial diffusion,
* artificial energy gain,
* mass loss,
* numerical instability.

This is one reason the choice of numerical method matters.

For example, **finite-volume methods** are especially popular in CFD because they discretize conservation laws in a way that preserves flux balances naturally.

A conservation law like

$$
\frac{\partial u}{\partial t} + \nabla\cdot\mathbf F=0
$$

is integrated over a cell:

$$
\frac{d}{dt} \int_V u,dV + \int_{\partial V} \mathbf F\cdot\mathbf n,dS = 0.
$$

This says:

> change inside the cell = flux through the cell boundary.

That maps beautifully onto a numerical grid.

---

## 8. Finite difference vs finite volume vs finite element

These are three major discretization philosophies.

### Finite difference

Approximate derivatives directly:

$$
u_{xx} \approx \frac{u_{i-1}-2u_i+u_{i+1}}{h^2}
$$
Best intuition:

> replace derivatives with algebraic formulas.

Very intuitive on structured grids.

### Finite volume

Integrate conservation laws over small cells.

Best intuition:

> track how much enters and leaves each cell.

This is why finite volume is heavily used in CFD.

### Finite element

Approximate the solution using basis functions:

$$
u_h(x) = \sum_i u_i\phi_i(x)
$$

Instead of enforcing the PDE point-by-point, the PDE is enforced in an integral or **weak** sense.

Best intuition:

> approximate the whole field using simple building blocks over small geometric elements.

This is particularly powerful for complicated geometries.

---

## 9. Why finite element needs a weak form

Take:

$$
-u''=f
$$
$$
Multiply both sides by a test function (v):
$$

$$
-u''v=fv
$$

Integrate:

$$
\int -u''v,dx = \int fv,dx
$$
Then integrate by parts:

$$
\int u'v'\,dx - \left[u'v\right]_{\partial\Omega} = \int fv\,dx
$$

Ignoring or handling the boundary term appropriately:

$$
\boxed{ \int u'v',dx = \int fv,dx }
$$

This is the weak form.

Why do this?

Because the original PDE required a second derivative:

$$
u''
$$
The weak form only requires first derivatives:

$$
u'
$$

That allows us to approximate $u$ using simpler functions.

This is one of the central mathematical ideas behind finite elements.

---

## 10. The finite-element field is built from basis functions

Suppose we divide the interval into elements:

```text
x0 ------ x1 ------ x2 ------ x3
```

At every node we define a basis function.

For example:

```text
φ1:

 /\
 / \

----/----\----------

 x0 x1 x2
```

and:

```text
φ2:

 /\
 / \

---------/----\------

 x1 x2 x3
```

Then write:

$$
u_h(x) = u_1\phi_1(x) + u_2\phi_2(x) + u_3\phi_3(x)
$$

The unknowns are only the coefficients:

$$
u_1,u_2,u_3
$$
Put this approximation into the weak form and you again obtain:

$$
A\mathbf u=\mathbf b
$$

Different path, same final numerical form.

---

## 11. So PDE solvers are largely matrix builders

A useful systems-level mental model is:

```text
PDE model
 ↓
geometry
 ↓
mesh
 ↓
discretization
 ↓
assemble matrices
 ↓
solve linear/nonlinear system
 ↓
field values
```

For a linear steady PDE:

$$
A\mathbf u=\mathbf b
$$
For nonlinear PDEs:

$$
F(\mathbf u)=0
$$

For transient PDEs:

$$
M\dot{\mathbf u}+F(\mathbf u)=0
$$
Then numerical algorithms such as:

* LU decomposition,
* conjugate gradient,
* GMRES,
* Newton's method,
* multigrid,
* Runge-Kutta,
* backward differentiation formulas,

do most of the computational work.

---

## 12. A useful connection to ML

This is where scientific ML becomes interesting.

A classical PDE solver computes:

$$
\text{inputs} \rightarrow \text{assemble PDE system} \rightarrow \text{numerically solve} \rightarrow u(x,t).
$$

Suppose you solve the same family of PDE problems millions of times.

For example:

$$
\text{different geometries/material parameters} \rightarrow \text{fluid field}
$$

A neural surrogate tries to learn:

$$
\mathcal G_\theta: \text{problem specification} \rightarrow u(x,t).
$$

Instead of solving $A\mathbf u=\mathbf b$. from scratch every time, you approximate the mapping directly.

That is part of the motivation behind:

* neural operators,
* Fourier Neural Operators,
* DeepONet,
* surrogate CFD,
* physics-informed learning.

But—and this is important—the ML model doesn't make the original PDE formulation irrelevant. The PDE defines the physical mapping the model is trying to approximate.

---

## The key mental model to keep

When you hear "PDE solver", don't imagine some symbolic engine manipulating $\nabla^2u=f$. For most real problems, think:

$$
\boxed{ \text{PDE} \rightarrow \text{discretize space/time} \rightarrow \text{large sparse algebraic system} \rightarrow \text{numerical linear algebra} }
$$

And the next major question is therefore not really about PDEs—it is:

> **How do we know whether the numerical solution is actually close to the true PDE solution?**

That takes us into mesh refinement, discretization error, stability, convergence, consistency, CFL conditions, residuals, and conservation error. Those concepts are what distinguish "the solver returned a number" from "the simulation is trustworthy."
