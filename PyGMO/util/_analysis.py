from PyGMO import *

class analysis:
    """
    This class contains the tools necessary for exploratory analysis of the
    search and fitness space of a given problem. Several tests can be conducted
    on a low-discrepancy sample of the search space or on an existing population.
    The aim is to gain insight into the problem properties and to aid algorithm
    selection.
    """

    def __init__(self,input_object,npoints=0,method='sobol',first=1):
        """
        Constructor of the analysis class from a problem or population object. Also calls
        analysis.sample when npoints>0 or by default when a population object is input.\n
        USAGE: analysis(input_object=prob [, npoints=1000, method='sobol', first=1])\n
        *input_object: problem or population object used to initialise the analysis.
        *npoints: number of points of the search space to sample. If a population is input,
        a random subset of its individuals of size npoints will be sampled (defaults to the
        whole population). If a problem is input, a set of size npoints will be selected
        using the specified method. In this case, no sampling is considered by default.
        *method: method used to sample the normalized search space. Used only when input_object
        is a problem. Options are:
                *'sobol': sampling based on sobol low-discrepancy sequence. Default option.
                *'lhs': latin hypersquare sampling.
                *'montecarlo': Monte Carlo (random) sampling.
        *first: used only when sampling with 'sobol'. Index of the first element of the sequence
        that will be included in the sample. Defaults to 1. If set to 0, point (0,0,...,0) will
        also be sampled.
        """
        self.npoints=0
        self.points=[]
        self.f=[]
        self.grad_npoints=0
        self.grad_points=[]
        self.grad=[]
        self.c=[]
        self.local_nclusters=0
        self.local_initial_npoints=0
        self.dim, self.cont_dim, self.int_dim, self.c_dim, self.ic_dim, self.f_dim = (0,0,0,0,0,0)
        self.fignum=0

        if isinstance(input_object,population):
            self.prob=input_object.problem
            self.pop=input_object
            if npoints==0:
                self.sample(len(self.pop),'pop')
            else:
                self.sample(npoints,'pop')
        elif isinstance(input_object,problem._base):
            self.prob=input_object
            self.pop=[]
            if npoints>0:
                self.sample(npoints,method,first)
        else:
            raise ValueError(
             "analysis: input either a problem or a population object to initialise the class")


    def sample(self, npoints, method='sobol', first=1):
        """
        Routine used to sample the search space.\n
        USAGE: analysis.sample(npoints=1000 [, method='sobol',first=1])\n
        *npoints: number of points of the search space to sample.
        *method: method used to sample the normalized search space. Options are:
                *'sobol': sampling based on sobol low-discrepancy sequence. Default option.
                *'lhs': latin hypersquare sampling.
                *'montecarlo': Monte Carlo (random) sampling.
                *'pop': sampling by selection of random individuals from a population. Can only
                be used when a population object has ben input to the constructor.
        *first: used only when sampling with 'sobol'. Index of the first element of the sequence
        that will be included in the sample. Defaults to 1. If set to 0, point (0,0,...,0) will
        also be sampled.\n
        The following parameters are stored as attributes:
        *analysis.npoints: number of points sampled.
        *analysis.points[number of points sampled][search dimension]: chromosome of points sampled.
        *analysis.f[number of points sampled][fitness dimension]: fitness vector of points sampled.
        *analysis.ub[search dimension]: upper bounds of search space.
        *analysis.lb[search dimension]: lower bounds of search space.
        *analysis.dim: search dimension, number of variables in search space
        *analysis.cont_dim: number of continuous variables in search space
        *analysis.int_dim: number of integer variables in search space
        *analysis.c_dim: number of constraints
        *analysis.ic_dim: number of inequality constraints
        *analysis.f_dim: fitness dimension, number of objectives
        """
        self.points=[]
        self.f=[]
        self.npoints=npoints
        self.lb=list(self.prob.lb)
        self.ub=list(self.prob.ub)  

        self.dim, self.cont_dim, self.int_dim, self.c_dim, self.ic_dim, self.f_dim = \
        self.prob.dimension, self.prob.dimension - self.prob.i_dimension, self.prob.i_dimension, self.prob.c_dimension, self.prob. ic_dimension, self.prob.f_dimension

        # if self.c_dim > 0:
        #     raise ValueError(
        #      "analysis.sample: this analyzer is not yet suitable for constrained optimisation")
        if self.npoints <= 0:
            raise ValueError(
             "analysis.sample: at least one point needs to be sampled")

        if method=='pop':
            poplength=len(self.pop)
            if poplength==0:
                raise ValueError(
                    "analysis.sample: method 'pop' specified but population object inexistant or void")
            elif poplength<npoints:
                raise ValueError(
                    "analysis.sample: it is not possible to sample more points than there are in the population via 'pop'")
            elif poplength==npoints:
                self.points=[list(self.pop[i].cur_x) for i in range(poplength)]
                self.f=[list(self.pop[i].cur_f) for i in range(poplength)]
            else:
                idx=range(poplength)
                try:
                    from numpy.random import randint
                except ImportError:
                    raise ImportError(
                        "analysis.sample needs numpy to run when sampling partially a population. Is it installed?")
                for i in range(poplength,poplength-npoints,-1):  
                    r=idx.pop(randint(i))
                    self.points.append(list(self.pop[r].cur_x))
                    self.f.append(list(self.pop[r].cur_f))
        elif method=='montecarlo':
            try:
                from numpy.random import random
            except ImportError:
                raise ImportError(
                    "analysis.sample needs numpy to run when sampling with montecarlo method. Is it installed?")
            for i in range(npoints):
                self.points.append([])
                for j in range(self.dim):
                    r=random()
                    r=(r*self.ub[j]+(1-r)*self.lb[j])
                    if j>=self.cont_dim:
                        r=round(r,0)
                    self.points[i].append(r)
                self.f.append(list(self.prob.objfun(self.points[i])))
        else:
            if method=='sobol':
                sampler=util.sobol(self.dim,first)
            elif method=='lhs':
                sampler=util.lhs(self.dim,npoints)
            else:
                raise ValueError(
                    "analysis.sample: method specified is not valid. choose 'sobol', 'lhs', 'montecarlo' or 'pop'")
            for i in range(npoints):
                temp=list(sampler.next()) #sample in the unit hypercube
                for j in range(self.dim):
                    temp[j]=temp[j]*self.ub[j]+(1-temp[j])*self.lb[j] #resize
                    if j>=self.cont_dim:
                        temp[j]=round(temp[j],0) #round if necessary
                self.points.append(temp)
                self.f.append(list(self.prob.objfun(temp)))

#f-DISTRIBUTION FEATURES
   
    def _skew(self):
        """
        Returns the skew of the f-distributions in the form of a list [fitness dimension].\n
        USAGE: analysis.skew()
        """
        try:
            import scipy as sp
        except ImportError:
            raise ImportError(
                "analysis.skew needs scipy to run. Is it installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.skew: sampling first is necessary")
        from scipy.stats import skew
        return skew(self.f).tolist()

    def _kurtosis(self):
        """
        Returns the kurtosis of the f-distributions in the form of a list [fitness dimension].\n
        USAGE: analysis.kurtosis()
        """
        try:
            import scipy as sp
        except ImportError:
            raise ImportError(
                "analysis.kurtosis needs scipy to run. Is it installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.kurtosis: sampling first is necessary")
        from scipy.stats import kurtosis
        return kurtosis(self.f).tolist()

    def _mean(self):
        """
        Returns the mean values of the f-distributions in the form of a list [fitness dimension].\n
        USAGE: analysis.mean()
        """
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.mean needs numpy to run. Is it installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.mean: sampling first is necessary")
        from numpy import mean
        return mean(self.f,0).tolist()

    def _var(self):
        """
        Returns the variances of the f-distributions in the form of a list [fitness dimension].\n
        USAGE: analysis.var()
        """
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.var needs numpy to run. Is it installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.var: sampling first is necessary")
        from numpy import var
        return var(self.f,0).tolist()

    def _ptp(self):
        """
        Returns the peak-to-peak range of the f-distributions in the form of a list [fitness dimension].\n
        USAGE: analysis.ptp()
        """
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.ptp needs numpy to run. Is it installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.ptp: sampling first is necessary")
        from numpy import ptp
        return ptp(self.f,0).tolist()

    def _percentile(self,p):
        """
        Returns the percentile(s) of the f-distributions specified in p in the form of a list [length p][fitness dimension].\n
        USAGE: analysis.percentile(p=[0,10,25,50,75,100])
        *p: percentile(s) to return. Can be a single float or a list.
        """
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.percentile needs numpy to run. Is it installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.percentile: sampling first is necessary")
        from numpy import percentile
        try:
            return [percentile(self.f,i,0).tolist() for i in p]
        except TypeError:
            return percentile(self.f,p,0).tolist()

    def plot_f_distr(self,save_fig=False):
        """
        Routine that plots the f-distributions in terms of density of probability
        of a fitness value in the sample considered.\n
        USAGE: analysis.plot_f_distr([save_fig=False])
        *save_fig: if True, figures generated with this plot will be saved to a directory.
        If False, they will be shown on screen. Defaults to False.
        """
        try:
            from scipy.stats import gaussian_kde
            from matplotlib.pyplot import plot,draw,title,show,legend,axes
        except ImportError:
            raise ImportError(
                "analysis.plot_f_distr needs scipy and matplotlib to run. Are they installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.plot_f_distr: sampling first is necessary")
        ax=axes()
        for i in range(self.f_dim):
            tmp=[]
            for j in range(self.npoints):
                tmp.append(self.f[j][i])
            x=sorted(tmp)
            kde=gaussian_kde(x)
            y=kde(x)
            ax.plot(x,y,label='objective '+str(i+1))
        title('F-Distributions')
        legend()
        f=ax.get_figure()
        if save_fig:
            import os
            if not os.path.exists('./temp_analysis_figures/'):
                os.makedirs('./temp_analysis_figures/')
            f.savefig('./temp_analysis_figures/figure_'+str(self.fignum)+'.png')
            self.fignum+=1
        else:
            show(f)

    def _n_peaks_f(self,nf=0):
        """
        Returns the number of peaks of the f-distributions in the form of a list [fitness dimension].\n
        USAGE: analysis.n_peaks_f([nf=100])
        *nf: discretisation of the f-distributions used to find their peaks. Defaults to npoints-1.
        """
        try:
            from numpy import array,zeros
            from scipy.stats import gaussian_kde
        except ImportError:
            raise ImportError(
                "analysis.n_peaks_f needs scipy, numpy and matplotlib to run. Are they installed?")
        if self.npoints==0:
            raise ValueError(
                "analysis.n_peaks_f: sampling first is necessary")
        if nf==0:
            nf=self.npoints-1
        elif nf<3:
            raise ValueError(
                "analysis.n_peaks_f: value of nf too small")
        npeaks=[]
        for i in range(self.f_dim):
            npeaks.append(0)
            f=[a[i] for a in self.f]
            kde=gaussian_kde(f)
            df=self._ptp()[i]/nf
            x=[min(f)]
            for j in range(0,nf):
                x.append(x[j]+df)
            y=kde(x)
            minidx=[0]
            k=1
            for (a,b,c) in zip(y[0:nf-1],y[1:nf],y[2:nf+1]):
                if a>b<c:
                    minidx.append(k)
                k+=1
            minidx.append(nf+1)
            mode_mass=[kde.integrate_box_1d(x[minidx[j]],x[minidx[j+1]-1]) for j in range(len(minidx)-1)]
            for mode in mode_mass:
                if mode>0.01:
                    npeaks[i]+=1
        return npeaks

    #ADD MORE FUNCTIONS IF NECESSARY

#BOX CONSTRAINT HYPERVOLUME COMPUTATION
    def _box_hv(self):
        """
        Returns the hypervolume defined by the box constraints imposed on the search variables.
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.box_hv: sampling first is necessary")
        hv=1
        for i in range(self.dim):
            hv=hv*(self.ub[i]-self.lb[i])
        return hv

#DEGREE OF LINEARITY AND CONVEXITY
    def _p_lin_conv(self,n_pairs=0,threshold=10**(-10)):
        """
        Tests the probability of linearity and convexity and the mean deviation from linearity of
        the f-distributions obtained. A pair of points (X1,F1),(X2,F2) from the sample is selected
        per test and a random convex combination of them is taken (Xconv,Fconv). For each objective,
        if F(Xconv)=Fconv within tolerance, the function is considered linear there. Otherwise, if
        F(Xconv)<Fconv, the function is considered convex. |F(Xconv)-Fconv| is the linear deviation.
        The average of all tests performed gives the overall result.\n
        NOTE: integer variables values are fixed during each of the tests and linearity or convexity
        is evaluated as regards the continuous part of the chromosome.\n
        USAGE: analysis.p_lin_conv([n_pairs=100,threshold=10**(-10)])
        *n_pairs: number of pairs of points used in the test.
        *threshold: tolerance considered to rate the function as linear or convex between two points.\n
        Returns a tuple of length 3 containing:
        *p_lin[fitness dimension]: probability of convexity [0,1].
        *p_conv[fitness dimension]: probability of linearity [0,1].
        *mean_dev[fitness dimension]: mean deviation from linearity as defined above.

        """
        if self.npoints==0:
            raise ValueError(
                "analysis.p_lin_conv: sampling first is necessary")
        if self.cont_dim==0:
            raise ValueError(
                "analysis.p_lin_conv: this test makes no sense for purely integer problems")
        if n_pairs==0:
            n_pairs=self.npoints
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.p_lin_conv needs numpy to run. Is it installed?")

        from numpy.random import random,randint
        from numpy import array
        p_lin=np.zeros(self.f_dim)
        p_conv=np.zeros(self.f_dim)
        mean_dev=np.zeros(self.f_dim)
        for i in range(n_pairs):
            i1=randint(self.npoints)
            i2=randint(self.npoints)
            while (i2==i1):
                i2=randint(self.npoints)
            r=random()
            x=r*array(self.points[i1])+(1-r)*array(self.points[i2])

            if self.cont_dim!=self.dim:
                x[self.cont_dim:]=self.points[i1][self.cont_dim:]
                f_lin=r*array(self.f[i1])+(1-r)*array(self.prob.objfun(self.points[i2][:self.cont_dim]+self.points[i1][self.cont_dim:]))
            else:
                f_lin=r*array(self.f[i1])+(1-r)*array(self.f[i2])

            f_real=array(self.prob.objfun(x))
            delta=f_lin-f_real
            mean_dev+=abs(delta)

            for j in range(self.f_dim):
                if abs(delta[j])<threshold:
                    p_lin[j]+=1
                elif delta[j]>0:
                    p_conv[j]+=1
        p_lin/=n_pairs
        p_conv/=n_pairs
        mean_dev/=n_pairs
        self.lin_conv_npairs=n_pairs
        return (list(p_lin),list(p_conv),list(mean_dev))

#META-MODEL FEATURES
    def _lin_reg(self):
        """
        Performs a linear regression on the sampled dataset, per objective.\n
        USAGE: analysis.lin_reg()\n
        Returns: tuple (w,r2)
        *w[fitness dimension][search dimension+1]: coefficients of the regression model.
        *r2[fitness dimension]: r square coefficient(s).
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.lin_reg: sampling first is necessary")
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.lin_reg needs numpy to run. Is it installed?")
        from numpy import array
        from numpy.linalg import lstsq
        A=[]
        w=[]
        sst=self._var()*self.npoints
        m=self._mean()
        ssr=np.zeros(self.f_dim)
        for i in range(self.npoints):
            A.append(self.points[i]+[1])
        A=array(A)
        for i in range(self.f_dim):
            b=[]
            for j in range(self.npoints):
                b.append(self.f[j][i])
            b=array(b)
            temp=lstsq(A,b)[0]
            w.append(list(temp))
            for j in range(self.npoints):
                ssr[i]+=(np.dot(temp,A[j])-m[i])**2
        r2=list(ssr/sst)
        return (w,r2)


    def _lin_reg_inter(self,interaction_order=2):
        """
        Performs a linear regression with interaction products on the sampled dataset, per objective.\n
        USAGE: analysis.lin_reg_inter([interaction_order=2])
        *interaction_order: order of interaction [2, search dimension]. Defaults to 2.\n
        Returns: tuple (w,r2)
        *w[fitness dimension][number of products+search dimension+1]: coefficients of the regression model,
        ordered as follows: highest order first, lexicographical.
        *r2[fitness dimension]: r square coefficient(s).
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.lin_reg_corr: sampling first is necessary")
        if interaction_order<2 or interaction_order>self.dim:
            raise ValueError(
                "analysis.lin_reg_corr: interaction order should be in range [2,dim]")
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.lin_reg_corr needs numpy to run. Is it installed?")
        from numpy import array
        from numpy.linalg import lstsq
        from itertools import combinations
        A=[]
        w=[]
        inter=[]
        for i in range(interaction_order,1,-1):
            inter=inter+list(combinations(range(self.dim),i))
        n_inter=len(inter)
        sst=self._var()*self.npoints
        m=self._mean()
        ssr=np.zeros(self.f_dim)
        for i in range(self.npoints):
            c=[]
            for j in range(n_inter):
                prod=1
                for k in range(len(inter[j])):
                    prod*=self.points[i][inter[j][k]]
                c.append(prod)
            A.append(c+self.points[i]+[1])
        A=array(A)
        for i in range(self.f_dim):
            b=[]
            for j in range(self.npoints):
                b.append(self.f[j][i])
            b=array(b)
            temp=lstsq(A,b)[0]
            w.append(list(temp))
            for j in range(self.npoints):
                ssr[i]+=(np.dot(temp,A[j])-m[i])**2
        r2=list(ssr/sst)
        return (w,r2)

    def _poly_reg(self,regression_degree=2):
        """
        Performs a polynomial regression on the sampled dataset, per objective.\n
        USAGE: analysis.poly_reg([regression_degree=2])
        *regression_degree: degree of regression >=2. Defaults to 2.\n
        Returns: tuple (w,r2)
        *w[fitness dimension][number of coefficients]: coefficients of the regression model,
        ordered as follows: highest order first, lexicographical.
        *r2[fitness dimension]: r square coefficient(s).
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.lin_reg_corr: sampling first is necessary")
        if regression_degree<2:
            raise ValueError(
                "analysis.lin_reg_corr: regression_degree needs to be >=2")
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.lin_reg_corr needs numpy to run. Is it installed?")
        from numpy import array
        from numpy.linalg import lstsq
        from itertools import combinations_with_replacement
        A=[]
        w=[]
        coef=[]
        for i in range(regression_degree,1,-1):
            coef=coef+list(combinations_with_replacement(range(self.dim),i))
        n_coef=len(coef)
        sst=self._var()*self.npoints
        m=self._mean()
        ssr=np.zeros(self.f_dim)
        for i in range(self.npoints):
            c=[]
            for j in range(n_coef):
                prod=1
                for k in range(len(coef[j])):
                    prod*=self.points[i][coef[j][k]]
                c.append(prod)
            A.append(c+self.points[i]+[1])
        A=array(A)
        for i in range(self.f_dim):
            b=[]
            for j in range(self.npoints):
                b.append(self.f[j][i])
            b=array(b)
            temp=lstsq(A,b)[0]
            w.append(list(temp))
            for j in range(self.npoints):
                ssr[i]+=(np.dot(temp,A[j])-m[i])**2
        r2=list(ssr/sst)
        return (w,r2)

#OBJECTIVE REDUNDANCY
    def _f_correlation(self):
        """
        Calculates the objective correlation matrix and its eigenvalues
        and eigenvectors. Only for multiobjective problems.\n
        USAGE: analysis.f_correlation()\n
        Returns: tuple (M,eval,evect)
        *M[search dimension][search dimension]: correlation matrix
        *eval[search dimension]: its eigenvalues
        *evect[search dimension][search dimension]: its eigenvectors
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.f_correlation: sampling first is necessary")
        if self.f_dim<2:
            raise ValueError(
                "analysis.f_correlation: this test makes no sense for single-objective optimisation")
        try:
            from numpy import corrcoef,transpose,dot
            from numpy.linalg import eigh
        except ImportError:
            raise ImportError(
                "analysis.f_correlation needs numpy to run. Is it installed?")
        M=corrcoef(self.f, rowvar=0)
        e=eigh(M)
        return (M.tolist(), e[0].tolist(), transpose(e[1]).tolist())
    
    def _perform_f_pca(self,obj_corr=None,tc=0.95,tabs=0.1):
        """
        Performs first Objective Reduction using Principal Component Analysis on
        the objective correlation matrix as defined in the reference and returns
        a list of the relevant objectives according to this procedure. Only for
        multiobjective problems.\n
        REF: Deb K. and Saxena D.K, On Finding Pareto-Optimal Solutions Through
        Dimensionality Reduction for Certain Large-Dimensional Multi-Objective
        Optimization Problems, KanGAL Report No. 2005011, IIT Kanpur, 2005.\n
        USAGE: analysis.perform_f_pca([obj_corr=None, tc=0.95, tabs=0.1])
        *obj_corr: objective correlation matrix, its eigenvalues and eigenvectors, in the
        form of the output of analysis.f_correlation. This parameter is added for reusability
        (if None, these will be calculated). Defaults to None.
        *tc: threshold cut. When the cumulative contribution of the eigenvalues absolute value
        equals this fraction of its maximum value, the reduction algorithm stops. A higher
        threshold cut means less reduction (see reference).
        *tabs: absolute tolerance. A Principal Component is treated differently if the
        absolute value of its corresponding eigenvalue is lower than this value (see
        reference).
        """
        try:
            from numpy import asarray,corrcoef,transpose,dot,argmax,argmin
            from numpy.linalg import eigh
            from itertools import combinations
        except ImportError:
            raise ImportError(
                "analysis.perform_f_pca needs numpy to run. Is it installed?")
        if obj_corr==None:
            obj_corr=self._f_correlation()
        M=obj_corr[0]
        eigenvals=obj_corr[1]
        eigenvects=obj_corr[2]
        #eigenvalue elimination of redundant objectives
        contributions=(asarray(abs(eigenvals))/sum(abs(eigenvals))).tolist()
        l=len(eigenvals)
        eig_order=[y for (x,y) in sorted(zip(contributions,range(l)),reverse=True)]
        cumulative_contribution=0
        keep=[]
        first=True
        for i in eig_order:
            index_p,index_n=argmax(eigenvects[i]),argmin(eigenvects[i])
            p,n=eigenvects[i][index_p],eigenvects[i][index_n]
            if first:
                first=False
                if p>0:
                    if all([k!=index_p for k in keep]):
                        keep.append(index_p)
                    if n<0:
                        if all([k!=index_n for k in keep]):
                            keep.append(index_n)
                else:
                    keep=range(l)
                    break
            elif abs(eigenvals[i])<tabs:
                if abs(p)>abs(n):
                    if all([k!=index_p for k in keep]):
                        keep.append(index_p)
                else:
                    if all([k!=index_n for k in keep]):
                        keep.append(index_n)
            else:
                if n>=0:
                    if all([k!=index_p for k in keep]):
                        keep.append(index_p)
                elif p<=0:
                    keep=range(l)
                    break
                else:
                    if abs(n)>=p>=0.9*abs(n):
                        if all([k!=index_p for k in keep]):
                            keep.append(index_p)
                        if all([k!=index_n for k in keep]):    
                            keep.append(index_n)
                    elif p<0.9*abs(n):
                        if all([k!=index_n for k in keep]):
                            keep.append(index_n)
                    else:
                        if abs(n)>=0.8*p:
                            if all([k!=index_p for k in keep]):
                                keep.append(index_p)
                            if all([k!=index_n for k in keep]):    
                                keep.append(index_n)
                        else:
                            if all([k!=index_p for k in keep]):
                                keep.append(index_p)

            cumulative_contribution+=contributions[i]
            if cumulative_contribution>=tc or len(keep)==l:
                break
        #correlation elimination of redundant objectives
        if len(keep)>2: 
            c=list(combinations(keep,2))
            for i in range(len(c)):
                if all([x*y>0 for x,y in zip(M[c[i][0]],M[c[i][1]])]) and any([k==c[i][1] for k in keep]) and any([k==c[i][0] for k in keep]):
                    if keep.index(c[i][0])<keep.index(c[i][1]):
                        keep.remove(c[i][1])
                    else:
                        keep.remove(c[i][0])
        return sorted(keep)
      

#CURVATURE
#possible problem: tolerance needs to be relative to the magnitude of the result
    def _get_gradient(self,sample_size=0,h=0.01,grad_tol=0.000001,zero_tol=0.000001):
        """
        Routine that selects points from the sample and calculates the Jacobian
        matrix in them by calling richardson_gradient. Also computes its sparsity.\n
        NOTE: all integer variables are ignored for this test.\n
        USAGE: analysis.get_gradient([sample_size=100, h=0.01, grad_tol=0.000001, zero_tol=0.000001])
        *sample_size: number of points from sample to calculate gradient at. If set
        to 0, all points will be used. Defaults to 0.
        *zero_tol: sparsity tolerance. For a position of the jacobian matrix to be
        considered a zero, its mean absolute value has to be <=zero_tol.
        The rest of parameters are passed to richardson_gradient.\n
        The following information is stored as attributes:
        *analysis.grad_npoints: number of points where jacobian is computed.
        *analysis.grad_points[grad_npoints]: indexes of these points in sample list.
        *analysis.grad[grad_npoints][fitness dimension][continuous search dimension]:
        jacobian matrixes computed.
        *analysis.average_abs_gradient[fitness dimension][continuous search dimension]:
        mean absolute value of jacobian matrixes computed.
        *analysis.grad_sparsity: fraction of zeroes in jacobian matrix.
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.get_gradient: sampling first is necessary")
        try:
            from numpy.random import randint
            from numpy import nanmean, asarray
        except ImportError:
            raise ImportError(
                "analysis.get_gradient needs numpy to run. Is it installed?")
        
        if sample_size<=0 or sample_size>=self.npoints:
            self.grad_points=range(self.npoints)
            self.grad_npoints=self.npoints
        else:
            self.grad_npoints=sample_size
            self.grad_points=[randint(self.npoints) for i in range(sample_size)] #avoid repetition?

        self.grad=[]
        self.grad_sparsity=0
        for i in self.grad_points:
            self.grad.append(self._richardson_gradient(x=self.points[i],h=h,grad_tol=grad_tol))
        self.average_abs_gradient=nanmean(abs(asarray(self.grad)),0)
        for i in range(self.f_dim):
            for j in range(self.cont_dim):
                if abs(self.average_abs_gradient[i][j])<=zero_tol:
                    self.grad_sparsity+=1.
        self.grad_sparsity/=(self.cont_dim*self.f_dim)

    def _richardson_gradient(self,x,h,grad_tol,tmax=15):
        """
        Evaluates jacobian matrix in point x of the search space by means of Richardson
        Extrapolation.\n
        NOTE: all integer variables are ignored for this test.\n
        USAGE: analysis.richardson_gradient(x=(a point's chromosome), h=0.01, grad_tol=0.000001 [, tmax=15])
        *x: list or tuple containing the chromosome of a point in the search space, where
        the Jacobian Matrix will be evaluated.
        *h: initial dx taken for evaluation of derivatives.
        *grad_tol: tolerance for convergence.
        *tmax: maximum of iterations. Defaults to 15.\n
        Returns jacobian matrix at point x as a list [fitness dimension][continuous search
        dimension]
        """
        from numpy import array, zeros, amax
        d=[[zeros([self.f_dim,self.cont_dim])],[]]
        hh=2*h
        err=1
        t=0
        while (err>grad_tol and t<tmax):
            hh/=2
            for i in range(self.cont_dim):
                xu=list(x)
                xd=list(x)
                xu[i]+=hh
                xd[i]-=hh
                tmp=(array(self.prob.objfun(xu))-array(self.prob.objfun(xd)))/(2*hh)
                
                for j in range(self.f_dim):
                    d[t%2][0][j][i]=tmp[j]

            for k in range(1,t+1):
                d[t%2][k]=d[t%2][k-1]+(d[t%2][k-1]-d[(t+1)%2][k-1])/(4**k-1)

            if t>0:
                err=amax(abs(d[t%2][t]-d[(t+1)%2][t-1]))

            d[(t+1)%2].extend([zeros([self.f_dim,self.cont_dim]),zeros([self.f_dim,self.cont_dim])])
            t+=1

        return d[(t+1)%2][t-1].tolist()


    def _get_hessian(self,sample_size=0,h=0.01,hess_tol=0.000001):
        """
        Routine that selects points from the sample and calculates the Hessian
        3rd-order tensor in them by calling richardson_hessian.\n
        NOTE: all integer variables are ignored for this test.\n
        USAGE: analysis.get_hessian([sample_size=100, h=0.01, hess_tol=0.000001])
        *sample_size: number of points from sample to calculate hessian at. If set
        to 0, all points will be used. Defaults to 0.
        The rest of parameters are passed to richardson_hessian.\n
        The following information is saved as attributes:
        *analysis.hess_npoints: number of points where hessian is computed.
        *analysis.hess_points[hess_npoints]: indexes of these points in sample list.
        *analysis.hess[hess_npoints][fitness dimension][continuous search dimension]
        [continuous search dimension]: hessian 3rd-order tensors computed.
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.get_hessian: sampling first is necessary")
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.get_hessian needs numpy to run. Is it installed?")
        from numpy.random import randint
        
        if sample_size<=0 or sample_size>=self.npoints:
            self.hess_points=range(self.npoints)
            self.hess_npoints=self.npoints

        else:
            self.hess_npoints=sample_size
            self.hess_points=[randint(self.npoints) for i in range(sample_size)] #avoid repetition?

        self.hess=[]
        for i in self.hess_points:
            self.hess.append(self._richardson_hessian(x=self.points[i],h=h,hess_tol=hess_tol))

    def _richardson_hessian(self,x,h,hess_tol,tmax=15):
        """
        Evaluates hessian 3rd-order tensor in point x of the search space by means of
        Richardson Extrapolation.\n
        NOTE: all integer variables are ignored for this test.\n
        USAGE: analysis.richardson_hessian(x=(a point's chromosome), h=0.01, hess_tol=0.000001 [, tmax=15])
        *x: list or tuple containing the chromosome of a point in the search space, where
        the Hessian 3rd-order tensor will be evaluated.
        *h: initial dx taken for evaluation of derivatives.
        *hess_tol: tolerance for convergence.
        *tmax: maximum of iterations. Defaults to 15.\n
        Returns hessian tensor at point x as a list [fitness dimension][continuous search
        dimension][continuous search dimension].
        """
        from numpy import array, zeros, amax
        from itertools import combinations_with_replacement
        ind=list(combinations_with_replacement(range(self.cont_dim),2))
        n_ind=len(ind)
        d=[[zeros([self.f_dim,n_ind])],[]]
        hh=2*h
        err=1
        t=0
        while (err>hess_tol and t<tmax):
            hh/=2
            for i in range(n_ind):
                xu=list(x)
                xd=list(x)
                xuu=list(x)
                xdd=list(x)
                xud=list(x)
                xdu=list(x)

                if ind[i][0]==ind[i][1]:
                    xu[ind[i][0]]+=hh
                    xd[ind[i][0]]-=hh

                    tmp=(array(self.prob.objfun(xu))-2*array(self.prob.objfun(x))+array(self.prob.objfun(xd)))/(hh**2)

                else:
                    xuu[ind[i][0]]+=hh
                    xuu[ind[i][1]]+=hh
                    xdd[ind[i][0]]-=hh
                    xdd[ind[i][1]]-=hh
                    xud[ind[i][0]]+=hh
                    xud[ind[i][1]]-=hh
                    xdu[ind[i][0]]-=hh
                    xdu[ind[i][1]]+=hh

                    tmp=(array(self.prob.objfun(xuu))-array(self.prob.objfun(xud))-array(self.prob.objfun(xdu))+array(self.prob.objfun(xdd)))/(4*hh*hh)

                for j in range(self.f_dim):
                    d[t%2][0][j][i]=tmp[j]

            for k in range(1,t+1):
                d[t%2][k]=d[t%2][k-1]+(d[t%2][k-1]-d[(t+1)%2][k-1])/(4**k-1)

            if t>0:
                err=amax(abs(d[t%2][t]-d[(t+1)%2][t-1]))

            d[(t+1)%2].extend([zeros([self.f_dim,n_ind]),zeros([self.f_dim,n_ind])])
            t+=1

        hessian=[]
        for i in range(self.f_dim):
            mat=zeros([self.cont_dim,self.cont_dim])
            for j in range(n_ind):
                mat[ind[j][0]][ind[j][1]]=d[(t+1)%2][t-1][i][j]
                mat[ind[j][1]][ind[j][0]]=d[(t+1)%2][t-1][i][j]
            hessian.append(mat.tolist())

        return hessian

    def plot_gradient_sparsity(self,zero_tol=0.0001,save_fig=False):
        """
        Plots sparsity of jacobian matrix. A position is considered a zero if its mean
        absolute value is lower than tolerance.\n
        USAGE: analysis.plot_gradient_sparsity([zero_tol=0.0001,save_fig=False])
        *zero_tol: tolerance.
        *save_fig: if True, figures generated with this plot will be saved to a directory.
        If False, they will be shown on screen. Defaults to False.
        """
        if self.grad_npoints==0:
            raise ValueError(
                "analysis.plot_gradient_sparsity: sampling and getting gradient first is necessary")
        try:
            from matplotlib.pylab import spy,show,title,grid,xlabel,ylabel,xticks,yticks,draw
            from numpy import nanmean,asarray
        except ImportError:
            raise ImportError(
                "analysis.plot_gradient_sparsity needs matplotlib and numpy to run. Are they installed?")

        
        title('Gradient/Jacobian Sparsity ('+str(100*round(self.grad_sparsity,4))+'% sparse) \n \n')
        grid(True)
        xlabel('dimension')
        ylabel('objective')
        plot=spy(self.average_abs_gradient,precision=zero_tol,markersize=20)
        try:
            xlocs=range(self.cont_dim)
            ylocs=range(self.f_dim)
            xlabels=[str(i) for i in range(1,self.cont_dim+1)]
            ylabels=[str(i) for i in range(1,self.f_dim+1)]
            xticks(xlocs,[x.format(xlocs[i]) for i,x in enumerate(xlabels)])
            yticks(ylocs,[y.format(ylocs[i]) for i,y in enumerate(ylabels)])
        except IndexError, ValueError:
            pass
        f=plot.get_figure()
        if save_fig:
            import os
            if not os.path.exists('./temp_analysis_figures/'):
                os.makedirs('./temp_analysis_figures/')
            f.savefig('./temp_analysis_figures/figure_'+str(self.fignum)+'.png')
            self.fignum+=1
        else:
            show(f)


    def plot_gradient_pcp(self,mode='x',scaled=True,save_fig=False):
        """
        Generates Parallel Coordinate Plot of Gradient.\n
        USAGE: analysis.plot_gradient_pcp([mode='x', scaled=True, save_fig=False])
        *mode: 2 options are available:
                *'x': parallel axes are search variables, colors are objectives.
                Not suitable for univariate problems.
                *'f': parallel axes are objectives, colors are search variables.
                Not suitable for single-objective problems.
        *scaled: if True, dFi/dXj will be scaled with peak-to-peak value of objective
        Fi divided by search-space width in variable Xj.
        *save_fig: if True, figures generated with this plot will be saved to a directory.
        If False, they will be shown on screen. Defaults to False.
        """
        if self.grad_npoints==0:
            raise ValueError(
                "analysis.plot_gradient_pcp: sampling and getting gradient first is necessary")
        if mode!='x' and mode!='f':
            raise ValueError(
                "analysis.plot_gradient_pcp: choose a valid value for mode ('x' or 'f')")
        if mode=='x' and self.cont_dim==1:
            raise ValueError(
                "analysis.plot_gradient_pcp: mode 'x' makes no sense for univariate problems")
        if mode=='f' and self.f_dim==1:
            raise ValueError(
                "analysis.plot_gradient_pcp: mode 'f' makes no sense for single-objective problems")
        try:
            from pandas.tools.plotting import parallel_coordinates as pc
            from pandas import DataFrame as df
            from matplotlib.pyplot import show,title,grid,ylabel,xlabel
            from numpy import asarray,transpose
        except ImportError:
            raise ImportError(
                "analysis.plot_gradient_pcp needs pandas, numpy and matplotlib to run. Are they installed?")
        gradient=[]
        if scaled:
            ranges=self._ptp()
        if mode=='x':
            aux=0
            rowlabel=True
        else:
            aux=1
            rowlabel=False
        for i in range(self.grad_npoints):
            if rowlabel:
                tmp=[]
            else:
                tmp=[['x'+str(x+1) for x in range(self.cont_dim)]]
            for j in range(self.f_dim):
                if rowlabel:
                    tmp.append(['objective '+str(j+1)])
                else:
                    tmp.append([])
                if scaled:
                    for k in range(self.cont_dim):
                        tmp[j+aux].append(self.grad[i][j][k]*(self.ub[k]-self.lb[k])/ranges[j])
                else:
                    tmp[j+aux].extend(self.grad[i][j])
            if rowlabel:
                gradient.extend(tmp)
            else:
                tmp2=[]
                for ii in range(self.cont_dim):
                    tmp2.append([])
                    for jj in range(self.f_dim+1):
                        tmp2[ii].append(tmp[jj][ii])
                gradient.extend(tmp2)
        gradient=df(gradient)

        title('Gradient PCP \n')
        grid(True)
        if scaled:
            scalelabel=' (scaled)'
        else:
            scalelabel=''
        ylabel('Derivative value'+scalelabel)
        if rowlabel:
            xlabel('Dimension')
        else:
            xlabel('Objective')
        plot=pc(gradient,0)
        f=plot.get_figure()
        if save_fig:
            import os
            if not os.path.exists('./temp_analysis_figures/'):
                os.makedirs('./temp_analysis_figures/')
            f.savefig('./temp_analysis_figures/figure_'+str(self.fignum)+'.png')
            self.fignum+=1
        else:
            show(f)

#LOCAL SEARCH -> minimization assumed, single objective assumed

    def _func(self,x,obj):#NOT IN USE

        return float(self.prob.objfun(x)[obj])

    def _get_local_extrema0(self,sample_size=0,method='Powell'):#NOT IN USE
        if self.npoints==0:
            raise ValueError(
                "analysis.get_local_extrema: sampling first is necessary")
        if (method=='Powell' or method=='Nelder-Mead' or method=='BFGS' or method=='CG')==False:
            raise ValueError(
                "analysis.get_local_extrema: choose a method amongst 'Powell', 'Nelder-Mead', 'BFGS' or 'CG'")
        try:
            import scipy as sp
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.get_local_extrema needs numpy and scipy to run. Are they installed?")
        from numpy.random import randint
        from scipy.optimize import minimize
        
        if sample_size<=0 or sample_size>=self.npoints:
            self.local_initial_points=range(self.npoints)
            self.local_initial_npoints=self.npoints
        else:
            self.local_initial_npoints=sample_size
            self.local_initial_points=[randint(self.npoints) for i in range(sample_size)] #avoid repetition?

        self.local_extrema=[]
        self.local_neval=[]
        self.local_f=[]
        for j in range(self.f_dim):
            tmp1=[]
            tmp2=[]
            tmp3=[]
            for i in self.local_initial_points:
                res=minimize(self._func,self.points[i],(j,),method)
                tmp1.append(list(res.x))
                tmp2.append(res.nfev)
                tmp3.append(res.fun)
            self.local_extrema.append(tmp1)
            self.local_neval.append(tmp2)
            self.local_f.append(tmp3)

    def _get_local_extrema(self,sample_size=0,algo=algorithm.gsl_fr(),par=True,decomposition_method='tchebycheff',weights='uniform',z=[],warning=True):
    #maybe cool to add con2un meta problem when handling constraint optimisation
        """
        Selects points from the sample and launches local searches using them as initial points.
        USAGE: analysis.get_local_extrema([sample_size=0, algo=algorithm.gsl_fr(), par=True, decomposition_method='tchebycheff', weights='uniform', z=[], warning=True)
        *sample_size: number of initial points to launch local searches from. If set to 0, all
        points in sample are used. Defaults to 0.
        *algo: algorithm object used in searches. For purposes it should be a local
        optimisation algorithm. Defaults to algorithm.gsl_fr().
        *par: if True, an unconnected archipelago will be used for possible parallelization.
        *decomposition_method: method used by problem.decompose in the case of multi-objective
        problems. Options are: 'tchebycheff', 'weighted', 'bi' (boundary intersection).
        Defaults to 'tchebycheff'.
        *weights: weight vector used by problem.decompose in the case of multi-objective
        problems. Options are: 'uniform', 'random' or any vector of length [fitness dimension]
        whose components sum to one. Defaults to 'uniform'.
        *z: ideal reference point used by 'tchebycheff' and 'bi' methods. If set to [] (empty
        vector), point (0,0,...,0) is used. Defaults to [].
        *warning: if True, a warning showing the decomposition method and parameters will be shown
        on screen when applying this test to a multi-objective problem.\n
        The following parameters are stored as attributes:
        *analysis.local_initial_npoints: number of initial points used for local searches (number
        of searches performed).
        *analysis.local_initial_points[number of searches]: index of each initial point in the
        list of sampled points. If the whole sample is used, the list is sorted.
        *analysis.local_search_time[number of searches]: time elapsed in each local search
        (miliseconds).
        *analysis.local_extrema [number of searches][search space dimension]: resulting point of
        each of the local searches.
        *analysis.local_f [number of searches]: fitness value of each resulting point (after
        fitness decomposition in multi-objective problems).\n
        """
        if self.npoints==0:
            raise ValueError(
                "analysis.get_local_extrema: sampling first is necessary")

        if not isinstance(algo,PyGMO.algorithm._algorithm._base):
            raise ValueError(
                "analysis.get_local_extrema: input a valid pygmo algorithm")
        try:
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.get_local_extrema needs numpy to run. Is it installed?")
        from numpy.random import randint
        from time import time
        
        if sample_size<=0 or sample_size>=self.npoints:
            self.local_initial_points=range(self.npoints)
            self.local_initial_npoints=self.npoints
        else:
            self.local_initial_npoints=sample_size
            self.local_initial_points=[randint(self.npoints) for i in range(sample_size)] #avoid repetition?

        self.local_extrema=[]
        #self.local_neval=[]// pygmo doesn't return it
        self.local_search_time=[]
        self.local_f=[]

        if self.f_dim==1:
            decomposition=self.prob
        else:
            if weights=='uniform':
                weightvector=[1./self.f_dim for i in range(self.f_dim)]
            elif weights=='random':
                weightvector=[]
            else:
                weightvector=weights

            decomposition=problem.decompose(self.prob,method=decomposition_method, weights=weightvector,z=z)
            if warning:
                if decomposition_method=='tchebycheff' or decomposition_method=='bi':
                    if z==[]:
                        z=[0 for i in range(self.f_dim)]
                    additional_message=' and '+str(z)+' ideal reference point!'
                else:
                    additional_message='!'
                print 'WARNING: get_local_extrema is decomposing multi-objective problem by means of ',decomposition_method,' method, with ',str(weights),'weight vector',additional_message
        if par:
            archi=archipelago()
        for i in range(self.local_initial_npoints):
            pop=population(decomposition)
            pop.push_back(self.points[self.local_initial_points[i]])
            isl=island(algo,pop)
            if par:
                archi.push_back(isl)
            else:
                isl.evolve(1)
                self.local_search_time.append(isl.get_evolution_time())
                self.local_extrema.append(isl.population.champion.x)
                self.local_f.append(isl.population.champion.f[0])
        if par:
            start=time()
            archi.evolve(1)
            archi.join()
            finish=time()
            for i in archi:
                self.local_search_time.append(i.get_evolution_time())
                self.local_extrema.append(i.population.champion.x)
                self.local_f.append(i.population.champion.f[0])


    def _cluster_local_extrema(self,variance_ratio=0.95,k=0,single_cluster_tolerance=0.0001,kmax=0):
        """
        Clusters the results of a set of local searches and orders the clusters ascendently
        as regards fitness value of its centroid (after fitness decomposition in the case of
        multi-objective problems).\n
        USAGE: analysis.cluster_local_extrema([variance_ratio=0.95, k=0, single_cluster_tolerance=0.0001, kmax=0])
        *variance_ratio: target fraction of variance explained by the cluster centroids
        when not clustering to a fixed number of clusters.
        *k: number of clusters when clustering to fixed number of clusters. If k=0, the
        clustering will be performed for increasing value of k until the explained variance
        ratio is achieved. Defaults to 0.
        *single_cluster_tolerance: if the radius of a single cluster is lower than this value
        times the search space dimension, k will be set to 1 when not clustering to a fixed
        number of clusters. Defaults to 0.0001.
        *kmax: maximum number of clusters admissible. If set to 0, the limit is the number
        of local searches performed. Defaults to 0.\n
        The following parameters are stored as attributes:
        *analysis.local_nclusters: number of clusters obtained.
        *analysis.local_cluster[number of searches]: cluster to which each point belongs.
        *analysis.local_cluster_size[number of clusters]: size of each cluster.
        *analysis.local_cluster_rx[number of clusters]: radius of each cluster in the search space.
        *analysis.local_cluster_df[number of clusters]: range of fitness value in the cluster (after
        decomposition in the case of multi-objective problems).
        *analysis.local_cluster_x_centers[number of clusters]: projection of the cluster centroid
        on the search space.
        *analysis.local_cluster_f_centers[number of clusters]: projection of the cluster centroid
        on the fitness value axis (after decomposition in the case of multi-objective problems).
        """
        if self.npoints==0:
            raise ValueError(
                "analysis_cluster_local_extrema: sampling first is necessary")
        if self.local_initial_npoints==0:
            raise ValueError(
                "analysis.cluster_local_extrema: getting local extrema first is necessary")
        try:
            import numpy as np
            import scipy as sp
            import sklearn as sk
        except ImportError:
            raise ImportError(
                "analysis.cluster_local_extrema needs numpy,scipy and sklearn to run. Are they installed?")
        from sklearn.cluster import KMeans

        dataset=np.zeros([self.local_initial_npoints,self.dim+1])#normalized dataset

        range_f=np.mean(np.ptp(self.f,0))
        mean_f=np.mean(self.f)

        if kmax==0:
            kmax=self.local_initial_npoints

        if range_f<single_cluster_tolerance:
            raise ValueError(
                "analysis_cluster_local_extrema: the results appear to be constant")
        for i in range(self.local_initial_npoints):
            for j in range(self.dim):
                dataset[i][j]=(self.local_extrema[i][j]-0.5*self.ub[j]-0.5*self.lb[j])/(self.ub[j]-self.lb[j])
            dataset[i][self.dim]=(self.local_f[i]-mean_f)/range_f
        if k!=0:#cluster to given number of clusters
            clust=KMeans(k)

            #storage of output
            local_cluster=list(clust.fit_predict(dataset))
            self.local_nclusters=k
            cluster_size=np.zeros(k)
            for i in range(self.local_initial_npoints):
                cluster_size[local_cluster[i]]+=1
            cluster_size=list(cluster_size)

        else:#find out number of clusters
            clust=KMeans(1)
            total_distances=clust.fit_transform(dataset)
            total_center=clust.cluster_centers_[0]
            total_radius=max(total_distances)
            if total_radius<single_cluster_tolerance*(self.dim+1):#single cluster scenario
                #storage of output
                local_cluster=list(clust.predict(dataset))
                self.local_nclusters=1
                cluster_size=[0]
                for i in range(self.local_initial_npoints):
                    cluster_size[local_cluster[i]]+=1
                cluster_size=list(cluster_size)
            else:
                k=2 #multiple cluster scenario
                var_tot=sum([x**2 for x in total_distances])
                var_ratio=0
                while var_ratio<=variance_ratio and k<=kmax:
                    clust=KMeans(k)
                    y=clust.fit_predict(dataset)
                    cluster_size=np.zeros(k)
                    var_exp=0
                    for i in range(self.local_initial_npoints):
                        cluster_size[y[i]]+=1
                    for i in range(k):
                        distance=np.linalg.norm(clust.cluster_centers_[i]-total_center)
                        var_exp+=cluster_size[i]*distance**2
                    var_ratio=var_exp/var_tot
                    k+=1
                #storage of output
                local_cluster=list(y)
                self.local_nclusters=k-1

        #more storage and reordering so clusters are ordered best to worst
        cluster_value=[clust.cluster_centers_[i][self.dim] for i in range(self.local_nclusters)]
        order=[x for (y,x) in sorted(zip(cluster_value,range(self.local_nclusters)))]

        self.local_cluster_x_centers=[]
        self.local_cluster_f_centers=[]
        self.local_cluster=[]
        self.local_cluster_size=[]
        for i in range(self.local_nclusters):
            self.local_cluster_size.append(cluster_size[order[i]])
            self.local_cluster_x_centers.append(clust.cluster_centers_[order[i]][:self.dim])
            self.local_cluster_f_centers.append(clust.cluster_centers_[order[i]][self.dim]*range_f+mean_f)
            for j in range(self.dim):
                self.local_cluster_x_centers[i][j]*=(self.ub[j]-self.lb[j])
                self.local_cluster_x_centers[i][j]+=0.5*(self.ub[j]+self.lb[j])
        for i in range(self.local_initial_npoints):
            for j in range(self.local_nclusters):
                if local_cluster[i]==order[j]:
                    self.local_cluster.append(j)
                    break

        #calculate cluster radius and center
        self.local_cluster_rx=[0 for i in range(self.local_nclusters)]
        f=[[] for i in range(self.local_nclusters)]
        for i in range(self.local_initial_npoints):
            c=self.local_cluster[i]
            if self.local_cluster_size[c]==1:
                f[c].append(0)
            else:
                rx=np.linalg.norm(np.asarray(self.local_extrema[i])-np.asarray(self.local_cluster_x_centers[c]))
                f[c].append(self.local_f[i])
                if rx>self.local_cluster_rx[c]:
                    self.local_cluster_rx[c]=rx
        self.local_cluster_df=[np.ptp(f[t],0).tolist() for t in range(self.local_nclusters)]

    def plot_local_cluster_pcp(self,together=True,save_fig=False):
        """
        Generates a Parallel Coordinate Plot of the clusters obtained for the local
        search results. The parallel axes represent the chromosome of the initial
        points of each local search and the colors are the clusters to which its local
        search resulting points belong.\n
        USAGE: analysis.plot_local_cluster_pcp([together=True, save_fig=False])
        *together: if True, a single plot will be generated. If False, each cluster
        will be presented in a separate plot. Defaults to True.
        *save_fig: if True, figures generated with this plot will be saved to a directory.
        If False, they will be shown on screen. Defaults to False.
        """
        if self.local_nclusters==0:
            raise ValueError(
                "analysis.plot_local_cluster_pcp: sampling, getting local extrema and clustering them first is necessary")
        if self.dim==1:
            raise ValueError(
                "analysis.plot_local_cluster_pcp: this makes no sense for univariate problems")
        try:
            from pandas.tools.plotting import parallel_coordinates as pc
            from pandas import DataFrame as df
            from matplotlib.pyplot import show,title,grid,ylabel,xlabel,legend,plot,subplot
            from numpy import asarray,transpose
        except ImportError:
            raise ImportError(
                "analysis.plot_gradient_pcp needs pandas, numpy and matplotlib to run. Are they installed?")
        if together:
            n=1
            dataset=[[[self.local_cluster[i]+1]+\
            [(self.points[self.local_initial_points[i]][j]-self.lb[j])/(self.ub[j]-self.lb[j]) for j in range(self.dim)]\
            for i in range(self.local_initial_npoints)]]
            dataset[0].sort()
            separatelabel=['' for i in range(self.local_nclusters)]
        else:
            n=self.local_nclusters
            dataset=[[] for i in range(self.local_nclusters)]
            for i in range(self.local_initial_npoints):
                dataset[self.local_cluster[i]].append([self.local_cluster[i]+1]+[(self.points[self.local_initial_points[i]][j]-self.lb[j])/(self.ub[j]-self.lb[j]) for j in range(self.dim)])
            separatelabel=[': cluster '+str(i+1) for i in range(self.local_nclusters)]
        flist=[]
        for i in range(n):
            dataframe=df(dataset[i])
            title('Local extrema clusters PCP'+separatelabel[i]+' \n')
            grid(True)
            xlabel('Dimension')
            plot=pc(dataframe,0)
            f=plot.get_figure()
            if save_fig:
                import os
                if not os.path.exists('./temp_analysis_figures/'):
                    os.makedirs('./temp_analysis_figures/')
                f.savefig('./temp_analysis_figures/figure_'+str(self.fignum)+'.png')
                self.fignum+=1
            else:
                show(f)
    
    def plot_local_cluster_scatter(self,dimensions=[],save_fig=False):
        """
        Generates a Scatter Plot of the clusters obtained for the local search results
        in the dimensions specified (up to 3). Centroids are also shown.\n
        USAGE: analysis.plot_local_cluster_scatter([dimensions=[1,2], save_fig=False])
        *dimensions: list of up to 3 dimensions in the search space that will be shown
        in the scatter plot. If set to [], the whole search space will be taken. An
        error will be raised when trying to plot more than 3 dimensions.
        *save_fig: if True, figures generated with this plot will be saved to a directory.
        If False, they will be shown on screen. Defaults to False.
        """
        if self.local_nclusters==0:
            raise ValueError(
                "analysis.plot_local_cluster_scatter: sampling, getting local extrema and clustering them first is necessary")
        if len(dimensions)==0:
            dimensions=range(self.dim)
        if len(dimensions)>3:
            raise ValueError(
                "analysis.plot_local_cluster_scatter: choose a maximum of 3 dimensions to plot")
        try:
            from matplotlib.pyplot import show,title,grid,legend,axes,figure
            from mpl_toolkits.mplot3d import Axes3D
            from matplotlib.cm import Set1
            from numpy import asarray,linspace
        except ImportError:
            raise ImportError(
                "analysis.plot_local_cluster_scatter needs numpy and matplotlib to run. Are they installed?")
        
        dataset=asarray([[(self.points[self.local_initial_points[i]][j]-self.lb[j])/(self.ub[j]-self.lb[j]) for j in dimensions] for i in range(self.local_initial_npoints)])
        centers=[[(self.local_cluster_x_centers[i][j]-self.lb[j])/(self.ub[j]-self.lb[j]) for j in dimensions] for i in range(self.local_nclusters)]
        colors=Set1(linspace(0,1,self.local_nclusters))
        if len(dimensions)==1:
            ax=axes()
            ax.scatter(dataset,[0 for i in range(self.local_initial_npoints)], c=[colors[i] for i in self.local_cluster])
            ax.set_xlim(0,1)
            ax.set_ylim(-0.1,0.1)
            ax.set_yticklabels([])
            ax.set_xlabel('x'+str(dimensions[0]+1))
            grid(True)
            for i in range(self.local_nclusters):
                ax.scatter(centers[i][0],0.005,marker='^',color=colors[i],s=100)
                ax.text(centers[i][0],0.01,'cluster '+str(i+1),horizontalalignment='center',verticalalignment='bottom',color=colors[i],rotation='vertical',size=12,backgroundcolor='w')
        elif len(dimensions)==2:
            ax=axes()
            ax.scatter(dataset[:,0],dataset[:,1],c=[colors[i] for i in self.local_cluster])
            ax.set_xlim(0,1)
            ax.set_ylim(0,1)
            ax.set_xlabel('x'+str(dimensions[0]+1))
            ax.set_ylabel('x'+str(dimensions[1]+1))
            grid(True)
            for i in range(self.local_nclusters):
                ax.scatter(centers[i][0],centers[i][1],marker='^',color=colors[i],s=100)
                ax.text(centers[i][0]+.02,centers[i][1],'cluster '+str(i+1),horizontalalignment='left',verticalalignment='center',color=colors[i],size=12,backgroundcolor='w')
        else:
            fig=figure()
            ax=Axes3D(fig)
            ax.scatter(dataset[:,0],dataset[:,1],dataset[:,2],c=[colors[i] for i in self.local_cluster])
            ax.set_xlim(0,1)
            ax.set_ylim(0,1)
            ax.set_zlim(0,1)
            ax.set_xlabel('x'+str(dimensions[0]+1))
            ax.set_ylabel('x'+str(dimensions[1]+1))
            ax.set_zlabel('x'+str(dimensions[2]+1))
            for i in range(self.local_nclusters):
                ax.scatter(centers[i][0],centers[i][1],centers[i][2],marker='^',color=colors[i],s=100)
                ax.text(centers[i][0],centers[i][1]+0.02,centers[i][2],'cluster '+str(i+1),horizontalalignment='left',verticalalignment='center',color=colors[i],size=12,backgroundcolor='w')
        title('Local extrema clusters scatter plot')
        f=ax.get_figure()
        if save_fig:
            import os
            if not os.path.exists('./temp_analysis_figures/'):
                os.makedirs('./temp_analysis_figures/')
            f.savefig('./temp_analysis_figures/figure_'+str(self.fignum)+'.png')
            self.fignum+=1
        else:
            show(f)

#LEVELSET FEATURES NOT IN USE AT ALL(quite bad unless improved)
    def _lda(self,threshold=50,tsp=0.1):
        if self.npoints==0:
            raise ValueError(
                "analysis.lda: sampling first is necessary")
        try:
            import numpy as np
            import sklearn as sk
        except ImportError:
            raise ImportError(
                "analysis.lda needs numpy and scikit-learn to run. Are they installed?")
        from sklearn.lda import LDA
        from numpy import zeros
        from numpy.random import random
        clf=LDA()
        mce=[]
        for i in range (self.f_dim):
            per=self._percentile(threshold)[i]
            dataset=[[],[]]
            y=[[],[]]
            for j in range (self.npoints):
                r=random()
                if r<tsp:
                    index=1
                else:
                    index=0
                dataset[index].append(self.points[j])
                if self.f[j][i]>per:
                    y[index].append(1)
                else:
                    y[index].append(0)
            clf.fit(dataset[0],y[0])
            mce.append(1-clf.score(dataset[1],y[1]))
        return mce

    def _qda(self,threshold=50,tsp=0.1):
        if self.npoints==0:
            raise ValueError(
                "analysis.qda: sampling first is necessary")
        try:
            import numpy as np
            import sklearn as sk
        except ImportError:
            raise ImportError(
                "analysis.qda needs numpy and scikit-learn to run. Are they installed?")
        from sklearn.qda import QDA
        from numpy import zeros
        from numpy.random import random
        clf=QDA()
        mce=[]
        for i in range (self.f_dim):
            per=self._percentile(threshold)[i]
            dataset=[[],[]]
            y=[[],[]]
            for j in range (self.npoints):
                r=random()
                if r<tsp:
                    index=1
                else:
                    index=0
                dataset[index].append(self.points[j])
                if self.f[j][i]>per:
                    y[index].append(1)
                else:
                    y[index].append(0)
            clf.fit(dataset[0],y[0])
            mce.append(1-clf.score(dataset[1],y[1]))
        return mce

    def _kfdac(self,threshold=50,tsp=0.1):
        if self.npoints==0:
            raise ValueError(
                "analysis.kfdac: sampling first is necessary")
        try:
            import numpy as np
            import mlpy
        except ImportError:
            raise ImportError(
                "analysis.kfdac needs numpy and mlpy to run. Are they installed?")
        from mlpy import KFDAC, KernelGaussian
        from numpy import zeros
        from numpy.random import random
        K=KernelGaussian()
        clf=KFDAC(kernel=K)
        mce=[]
        for i in range (self.f_dim):
            per=self._percentile(threshold)[i]
            dataset=[[],[]]
            y=[[],[]]
            for j in range (self.npoints):
                r=random()
                if r<tsp:
                    index=1
                else:
                    index=0
                dataset[index].append(self.points[j])
                if self.f[j][i]>per:
                    y[index].append(1)
                else:
                    y[index].append(0)
            clf.learn(dataset[0],y[0])
            y_pred=clf.pred(dataset[1])
            score=(y_pred ==y[1])
            mce.append(1-np.mean(score))
        return mce

    def _knn(self,threshold=50,tsp=0.1): #highly unuseful at the moment
        if self.npoints==0:
            raise ValueError(
                "analysis.knn: sampling first is necessary")
        try:
            import numpy as np
            import sklearn as sk
        except ImportError:
            raise ImportError(
                "analysis.knn needs numpy and scikit-learn to run. Are they installed?")
        from sklearn.neighbors import KNeighborsClassifier
        from numpy import zeros
        from numpy.random import random
        clf=KNeighborsClassifier(weights='distance')
        mce=[]
        for i in range (self.f_dim):
            per=self._percentile(threshold)[i]
            dataset=[[],[]]
            y=[[],[]]
            for j in range (self.npoints):
                r=random()
                if r<tsp:
                    index=1
                else:
                    index=0
                dataset[index].append(self.points[j])
                if self.f[j][i]>per:
                    y[index].append(1)
                else:
                    y[index].append(0)
            clf.fit(dataset[0],y[0])
            mce.append(1-clf.score(dataset[1],y[1]))
        return mce

#LEVELSET FEATURES WITH DAC, IMPROVED BUT IN PRINCIPLE WORSE THAN SVM
    def _dac(self,threshold=50,classifier='k',k_test=10):
        if self.npoints==0:
            raise ValueError(
                "analysis.dac: sampling first is necessary")
        if classifier!='l' and classifier!= 'q' and classifier!='k':
            raise ValueError(
                "analysis.dac: choose a proper value for classifier ('l','q','k')")
        if threshold<=0 or threshold>=100:
            raise ValueError(
                "analysis.dac: threshold needs to be a value ]0,100[")
        try:
            import numpy as np
            import sklearn as sk
            import mlpy
        except ImportError:
            raise ImportError(
                "analysis.svm needs numpy, mlpy and scikit-learn to run. Are they installed?")
        from sklearn.cross_validation import StratifiedKFold, cross_val_score
        from sklearn.lda import LDA
        from sklearn.qda import QDA
        from sklearn.metrics import accuracy_score
        from mlpy import KFDAC, KernelGaussian

        if classifier=='l':
            clf=LDA()
        elif classifier=='q':
            clf=QDA()
        else:
            clf=KFDAC(kernel=KernelGaussian())
        per=self._percentile(threshold)
        
        dataset=[] #normalization of data
        for i in range(self.npoints):
            dataset.append(np.zeros(self.dim))
            for j in range(self.dim):
                dataset[i][j]=(self.points[i][j]-0.5*self.ub[j]-0.5*self.lb[j])/(self.ub[j]-self.lb[j])

        mce=[]
        for obj in range(self.f_dim):
            y=np.zeros(self.npoints) #classification of data
            for i in range(self.npoints):
                if self.f[i][obj]>per[obj]:
                    y[i]=1

            if classifier=='k':
                iterator=StratifiedKFold(y,k_test)
                i=0
                mce.append([])
                for train_index,test_index in iterator:
                    Xtrain=[]
                    Xtest=[]
                    ytrain=[]
                    ytest=[]
                    for i in train_index:
                        Xtrain.append(dataset[i])
                        ytrain.append(y[i])
                    for i in test_index:
                        Xtest.append(dataset[i])
                        ytest.append(y[i])
                    clf.learn(Xtrain,ytrain)
                    mce[obj].append(1-accuracy_score(clf.pred(Xtest),ytest))
            else:
                test_score=cross_val_score(estimator=clf,X=dataset,y=y,scoring=None,cv=StratifiedKFold(y,k_test))
                mce.append(list(np.ones(k_test)-test_score))

        return mce #mce[n_obj][k_test]

    def _dac_p_values(self,threshold=50,k_test=10):
        if self.npoints==0:
            raise ValueError(
                "analysis.dac_p_values: sampling first is necessary")
        try:
            import scipy as sp
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.dac_p_values needs scipy and numpy to run. Is it installed?")
        linear=self._dac(threshold=threshold, classifier='l', k_test=k_test)
        quadratic=self._dac(threshold=threshold, classifier='q', k_test=k_test)
        nonlinear=self._dac(threshold=threshold, classifier='k', k_test=k_test)
        l_q=[]
        q_n=[]
        l_n=[]
        for i in range(self.f_dim):
            l_q.append(sp.stats.mannwhitneyu(linear[i],quadratic[i])[1])
            l_n.append(sp.stats.mannwhitneyu(linear[i],nonlinear[i])[1])
            q_n.append(sp.stats.mannwhitneyu(quadratic[i],nonlinear[i])[1])
        return (list(np.mean(linear,1)),list(np.mean(quadratic,1)),list(np.mean(nonlinear,1)),l_q,l_n,q_n)

#LEVELSET FEATURES WITH SVM (PREFERABLY USE THESE...?)
    def _svm(self,threshold=50,kernel='rbf',k_tune=3,k_test=10):
        if self.npoints==0:
            raise ValueError(
                "analysis.svm: sampling first is necessary")
        if kernel!='linear' and kernel!= 'quadratic' and kernel!='rbf':
            raise ValueError(
                "analysis.svm: choose a proper value for kernel ('linear','quadratic','rbf')")
        if threshold<=0 or threshold>=100:
            raise ValueError(
                "analysis.svm: threshold needs to be a value ]0,100[")
        try:
            import numpy as np
            import sklearn as sk
        except ImportError:
            raise ImportError(
                "analysis.svm needs numpy and scikit-learn to run. Are they installed?")
        from sklearn.cross_validation import StratifiedKFold, cross_val_score
        from sklearn.svm import SVC
        from sklearn.grid_search import GridSearchCV
        from sklearn.preprocessing import StandardScaler
        if kernel=='quadratic':
            kernel='poly'
        c_range=2.**np.arange(-5,16)
        if kernel=='linear':
            param_grid=dict(C=c_range)
        else:
            g_range=2.**np.arange(-15,4)
            param_grid=dict(gamma=g_range,C=c_range)
        per=self._percentile(threshold)
        
        dataset=[] #normalization of data
        for i in range(self.npoints):
            dataset.append(np.zeros(self.dim))
            for j in range(self.dim):
                dataset[i][j]=(self.points[i][j]-0.5*self.ub[j]-0.5*self.lb[j])/(self.ub[j]-self.lb[j])

        mce=[]
        for obj in range(self.f_dim):
            y=np.zeros(self.npoints) #classification of data
            for i in range(self.npoints):
                if self.f[i][obj]>per[obj]:
                    y[i]=1

            #grid search
            grid=GridSearchCV(estimator=SVC(kernel=kernel,degree=2),param_grid=param_grid,cv=StratifiedKFold(y,k_tune))
            grid.fit(dataset,y)
            #print grid.best_estimator_
            test_score=cross_val_score(estimator=grid.best_estimator_,X=dataset,y=y,scoring=None,cv=StratifiedKFold(y,k_test))
            mce.append(list(np.ones(k_test)-test_score))

        return mce #mce[n_obj][k_test]

    def _svm_p_values(self,threshold=50,k_tune=3,k_test=10):
        if self.npoints==0:
            raise ValueError(
                "analysis.svm_p_values: sampling first is necessary")
        try:
            import scipy as sp
            import numpy as np
        except ImportError:
            raise ImportError(
                "analysis.svm_p_values needs scipy and numpy to run. Is it installed?")
        linear=self._svm(threshold=threshold, kernel='linear',k_tune=k_tune, k_test=k_test)
        quadratic=self._svm(threshold=threshold, kernel='quadratic',k_tune=k_tune, k_test=k_test)
        nonlinear=self._svm(threshold=threshold, kernel='rbf',k_tune=k_tune, k_test=k_test)
        l_q=[]
        q_n=[]
        l_n=[]
        for i in range(self.f_dim):
            l_q.append(sp.stats.mannwhitneyu(linear[i],quadratic[i])[1])
            l_n.append(sp.stats.mannwhitneyu(linear[i],nonlinear[i])[1])
            q_n.append(sp.stats.mannwhitneyu(quadratic[i],nonlinear[i])[1])
        return (list(np.mean(linear,1)),list(np.mean(quadratic,1)),list(np.mean(nonlinear,1)),l_q,l_n,q_n)


#CONSTRAINTS
    def _compute_constraints(self):
        if self.npoints==0:
            raise ValueError(
                "analysis.compute_constraints: sampling first is necessary")
        self.c=[]
        if self.c_dim!=0:
            for i in range(self.npoints):
                self.c.append(list(self.prob.compute_constraints(self.points[i])))

    def _ic_effectiveness(self):
        if self.npoints==0:
            raise ValueError(
                "analysis.constraint_feasibility: sampling first is necessary")
        ic_ef=[]
        if self.ic_dim!=0:
            if len(self.c)==0:
                raise ValueError(
                    "analysis.constraint_feasibility: compute constraints first")
            for i in range(self.ic_dim):
                ic_ef.append(0)
            dp=1./self.npoints
            for i in range(self.npoints):
                for j in range(-self.ic_dim,0):
                    if self.c[i][j]>=0:
                        ic_ef[j]+=dp
            return ic_ef

    def _ec_feasibility(self):
        if self.npoints==0:
            raise ValueError(
                "analysis.constraint_feasibility: sampling first is necessary")
        ec_f=[]
        if self.ic_dim-self.c_dim!=0:
            if len(self.c)==0:
                raise ValueError(
                    "analysis.constraint_feasibility: compute constraints first")
            for i in range(self.c_dim-self.ic_dim):
                ec_f.append(False)
                for j in range(self.npoints):
                    if self.c[j][i]==0 or (self.c[j][i]>0 and self.c[0][i]<0) or (self.c[0][i]>0 and self.c[j][i]<0):
                        ec_f[i]=True
            return ec_f

    #PRESENTATION OF RESULTS

    def _print_report(self,b1=True,sample=100,p_f=[0,10,25,50,75,90,100],b2=True,b20=True,p_svm=[],p_dac=[],local_search=True,\
    gradient=True,hessian=False,b3=True,b41=True,b42=True,b43=True,b51=True,b52=True,b60=True,b63=True,b64=True,b65=True,b66=False,\
    b711=True,b712=True,b713=True,i1=0,s3=0,s42=0,s43=0,s51=50,s52=50,s53=10,s54=3,s55=10,s6=0,i61=0,s61=0.95,s62=1,s63=[],i66=0,s661='random',s662='0',save=False,pca=False):
        import numpy as np
        import Tkinter as tk
        from ttk import Notebook, Frame
        import matplotlib
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
        from PIL import Image, ImageTk
        import os
        if b1 and i1==0:
            self.sample(sample,'sobol')
        if b1 and i1==1:
            self.sample(sample,'lhs')
        if b20:
            print "--------------------------------------------------------------------------------\n"
            print "PROBLEM PROPERTIES \n"
            print "--------------------------------------------------------------------------------\n"
            print "Dimension :                             ",self.dim," \n"
            print "     of which integer :                 ",self.int_dim," \n"
            print "Number of objectives :                  ",self.f_dim," \n"
            print "Number of constraints :                 ",self.c_dim," \n"
            print "     of which inequality constraints :  ",self.ic_dim," \n"
            print "Variable bounds : \n"
            for i in range(self.dim):
                print "     variable",i+1,":                       ","[",self.lb[i],",",self.ub[i],"]\n"
            # print "Box constraints hypervolume :           ",self._box_hv()," \n"
            print "--------------------------------------------------------------------------------\n"
            print "F-DISTRIBUTION FEATURES (",self.f_dim," OBJECTIVES )\n"
            print "--------------------------------------------------------------------------------\n"
            print "Number of points sampled :              ",self.npoints," \n"
            print "Range of objective function :           ",list(self._ptp())," \n"
            print "Mean value :                            ",list(self._mean())," \n"
            print "Variance :                              ",list(self._var())," \n"
            if len(p_f)>0:
                print "Percentiles : \n"
                for i in p_f:
                    if i<10:
                        print "     ",i,":                               ",list(self._percentile(i))," \n"
                    elif i==100:
                        print "     ",i,":                             ",list(self._percentile(i))," \n"
                    else:
                        print "     ",i,":                              ",list(self._percentile(i))," \n"  
            print "Skew :                                  ",list(self._skew())," \n"
            print "Kurtosis :                              ",list(self._kurtosis())," \n"
            print "Number of peaks of f-distribution :     ",self._n_peaks_f()," \n"
        if b41 or b42 or b43:
            print "--------------------------------------------------------------------------------\n"
            print "META-MODEL FEATURES \n"
            print "--------------------------------------------------------------------------------\n"
        if b41:
            print "Linear regression R2 :                  ",self._lin_reg()[1]," \n"
        if b42 and self.dim>=2 and len(s42)>0:
            for i in s42:
                print "Lin. regression with interaction (",i,") R2 :",self._lin_reg_inter(interaction_order=i)[1]," \n"
        if b43 and len(s43)>0:
            for i in s43:
                if i==2:
                    print "Quadratic regression R2 :               ",self._poly_reg(regression_degree=i)[1]," \n"
                else:
                    print "Polynomial regression degree", i ,"R2 : ",self._poly_reg(regression_degree=i)[1]," \n"
        if b51 and len(p_svm)>0:
            print "--------------------------------------------------------------------------------\n"
            print "LEVELSET FEATURES : SVM\n"
            print "--------------------------------------------------------------------------------\n"
            for i in p_svm:
                svm_results=self._svm_p_values(threshold=i,k_test=s53,k_tune=s54)
                print "Percentile",i,":\n"
                print "     Mean Misclassification Errors :\n"
                print "         Linear Kernel :                ",svm_results[0]," \n"
                print "         Quadratic Kernel :             ",svm_results[1]," \n"
                print "         Non-Linear Kernel (RBF):       ",svm_results[2]," \n"
                print "     P-Values : \n"
                print "         Linear/Quadratic :             ",svm_results[3]," \n"
                print "         Linear/Nonlinear :             ",svm_results[4]," \n"
                print "         Quadratic/Nonlinear :          ",svm_results[5]," \n"
        if b52 and len(p_dac)>0:
            print "--------------------------------------------------------------------------------\n"
            print "LEVELSET FEATURES : DAC\n"
            print "--------------------------------------------------------------------------------\n"
            for i in p_dac:
                dac_results=self._dac_p_values(threshold=i,k_test=s55)
                print "Percentile",i,":\n"
                print "     Mean Misclassification Errors :\n"
                print "         LDA :                          ",dac_results[0]," \n"
                print "         QDA :                          ",dac_results[1]," \n"
                print "         KFDA (RBF Kernel):             ",dac_results[2]," \n"
                print "     P-Values : \n"
                print "         Linear/Quadratic :             ",dac_results[3]," \n"
                print "         Linear/Nonlinear :             ",dac_results[4]," \n"
                print "         Quadratic/Nonlinear :          ",dac_results[5]," \n"
        if b3:
            print "--------------------------------------------------------------------------------\n"
            print "PROBABILITY OF LINEARITY AND CONVEXITY\n"
            print "--------------------------------------------------------------------------------\n"
            p=self._p_lin_conv(s3)
            print "Number of pairs of points used :        ",self.lin_conv_npairs," \n"
            print "Probability of linearity :              ",p[0]," \n"
            print "Probability of convexity :              ",p[1]," \n"
            print "Mean deviation from linearity :         ",p[2]," \n"
        if self.c_dim==0 and local_search:
            print "--------------------------------------------------------------------------------\n"
            print "LOCAL SEARCH\n"
            print "--------------------------------------------------------------------------------\n"
            if b66:
                self._get_local_extrema(sample_size=s6,algo=ls_algo,decomposition_method=i66,weights=s661,z=s662)
            else:
                self._get_local_extrema(sample_size=s6,decomposition_method=i66,weights=s661,z=s662)
            if b60:
                if i61==0:
                    self._cluster_local_extrema(variance_ratio=s61,k=0)
                else:
                    self._cluster_local_extrema(variance_ratio=0,k=s62)
            print "Local searches performed :              ",self.local_initial_npoints," \n"
            print "Quartiles of CPU time per search [ms]:  ",round(np.percentile(self.local_search_time,0),3),"/",round(np.percentile(self.local_search_time,25),3),"/",round(np.percentile(self.local_search_time,50),3),"/",round(np.percentile(self.local_search_time,75),3),"/",round(np.percentile(self.local_search_time,100),3)," \n"
            if b60:
                print "Number of clusters identified :         ",self.local_nclusters," \n"
                print "Cluster properties (max. best 5 clusters): \n"
                for i in range(min((self.local_nclusters,5))):
                    print "     Cluster n.:                        ",i+1," \n"
                    print "         Size:                          ",self.local_cluster_size[i],", ",100*round(self.local_cluster_size[i]/self.local_initial_npoints,4),"% \n"
                    print "         Mean objective value :         ",self.local_cluster_f_centers[i]," \n"
                    print "         Cluster center :               ",self.local_cluster_x_centers[i]," \n"
                    print "         Cluster diameter in F :        ",self.local_cluster_df[i]," \n"
                    print "         Cluster radius in X :          ",self.local_cluster_rx[i]," \n"
        if gradient:
            print "--------------------------------------------------------------------------------\n"
            print "CURVATURE : GRADIENT/JACOBIAN \n"
            print "--------------------------------------------------------------------------------\n"
            self._get_gradient()
            print "Number of points evaluated :            ",self.grad_npoints," \n"
            print "Gradient sparsity :                     ",100*round(self.grad_sparsity,4),"% \n"
        if hessian:
            print "--------------------------------------------------------------------------------\n"
            print "CURVATURE : HESSIAN \n"
            print "--------------------------------------------------------------------------------\n"
            self._get_hessian()
            print "Number of points evaluated :            ",self.hess_npoints," \n"
            
        if self.f_dim>1 and pca:
            print "--------------------------------------------------------------------------------\n"
            print "OBJECTIVE CORRELATION \n"
            print "--------------------------------------------------------------------------------\n"
            obj_corr=self._f_correlation()
            critical_obj=self._perform_f_pca(obj_corr)
            print "Objective correlation matrix :          ",obj_corr[0][0]," \n"
            for i in range(1,self.f_dim):
                print "                                        ",obj_corr[0][i]," \n"
            print "Eigenvalues (squared) :                 ",obj_corr[1]," \n"
            print "Eigenvalue relative contribution :      ",[str(100*round(i,4))+'%' for i in (np.asarray(obj_corr[1])/sum(obj_corr[1])).tolist()]," \n"
            print "Eigenvectors :                          ",obj_corr[2][0]," \n"
            for i in range(1,self.f_dim):
                print "                                        ",obj_corr[2][i]," \n"
            print "Critical objectives from first PCA :    ",[int(i) for i in (np.ones(len(critical_obj))+np.asarray(critical_obj)).tolist()]," \n"
        if self.c_dim>0:
            print "--------------------------------------------------------------------------------\n"
            print "CONSTRAINT EFFECTIVENESS/FEASIBILITY \n"
            print "--------------------------------------------------------------------------------\n"
            self._compute_constraints()
            ic_ef=self._ic_effectiveness()
            ec_f=self._ec_feasibility()
            if self.c_dim!=self.ic_dim:
                print "     Equality constraint      |      Feasibility   \n"
            for i in range(self.c_dim-self.ic_dim):
                print "            ",i+1,"                        ",ec_f[i],"       \n"
            if self.ic_dim>0:
                print "    Inequality constraint     |     Effectiveness   \n"
            for i in range(self.ic_dim):
                print "            ",self.c_dim-self.ic_dim+i+1,"                       ",100*round(ic_ef[i],4),"%      \n"
        #PLOTS
        old_fignum=self.fignum
        if b2:
            self.plot_f_distr(save_fig=save)

        if gradient:
            if b711:
                self.plot_gradient_sparsity(save_fig=save)

            if self.dim>1 and b712:
                self.plot_gradient_pcp('x',save_fig=save)

            if self.f_dim>1 and b713:
                self.plot_gradient_pcp('f',save_fig=save)

        if self.c_dim==0 and local_search:
            if b64:
                self.plot_local_cluster_pcp(together=True,save_fig=save)

            if b65:
                self.plot_local_cluster_pcp(together=False,save_fig=save)

            if b63:
                self.plot_local_cluster_scatter(save_fig=save)

        # #show plots in only window - DOESN'T WORK
        # if self.fignum>old_fignum:
        #     root=tk.Toplevel()
        #     root.title("PLOTS")
        #     n=Notebook(root)
        #     canvas=[]
        #     images=[]
        #     labels=[]
        #     ii=-1
        #     for i in range(old_fignum,self.fignum):
        #         canvas.append(tk.Canvas())
        #         images.append(ImageTk.PhotoImage(Image.open('./temp_analysis_figures/figure_'+str(i)+'.png')))
        #         ii+=1
        #         print canvas
        #         print images
        #         print ii
        #         canvas[ii].create_image(0,0,image=images[ii])
        #         # labels[ii].grid(row=0,column=0)
        #         n.add(canvas[ii],text='plot '+str(ii+1))
        #     n.pack()
        #     root.mainloop()

    def start(self):
        import Tkinter as tk
        from Tkinter import Tk, Frame, Checkbutton, Label, Entry, Radiobutton, Button
        from Tkinter import IntVar,BooleanVar, StringVar, BOTH


        class parameters(Frame):
  
            def __init__(self, parent):
                Frame.__init__(self, parent)   
                 
                self.parent = parent        
                self.initUI()
                
            def initUI(self):
              
                self.parent.title("ANALYSIS")

                self.pack(fill=BOTH, expand=1)

                self.b1=BooleanVar()#sample
                self.s1=StringVar()#number of points
                self.i1=IntVar()#sobol/lhs

                self.b2=BooleanVar()#plot f-distributions
                self.s2=StringVar()#percentiles
                self.b20=BooleanVar()#print basic problem info

                self.b3=BooleanVar()#perform lin_conv test
                self.s3=StringVar()#number of pairs

                self.b41=BooleanVar()#linear reg
                self.b42=BooleanVar()#linear reg w/ interaction
                self.s42=StringVar()#order of interaction
                self.b43=BooleanVar()#poly reg
                self.s43=StringVar()#degree of regression

                self.b51=BooleanVar()#SVM
                self.s51=StringVar()#threshold svm
                self.b52=BooleanVar()#DAC
                self.s52=StringVar()#threshold dac
                self.s53=StringVar()#ktest svn
                self.s54=StringVar()#ktune svn
                self.s55=StringVar()#ktest dac

                self.b6=BooleanVar()#perform local search
                self.s6=StringVar()#number of initial points
                self.b60=BooleanVar()#cluster results
                self.i61=IntVar()#var_ratio/k
                self.s61=StringVar()#var_ratio
                self.s62=StringVar()#k
                self.b63=BooleanVar()#scatter plot
                self.s63=StringVar()#scatter plot dimensions
                self.b64=BooleanVar()#PCP together
                self.b65=BooleanVar()#PCP separate
                self.b66=BooleanVar()#adv/use custom algo
                self.i66=IntVar()#adv/decomposition method
                self.s661=StringVar()#adv/decomposition weights
                self.s662=StringVar()#adv/z

                self.b71=BooleanVar()#get gradient
                self.b72=BooleanVar()#get hessian
                self.b711=BooleanVar()#gradient sparsity plot
                self.b712=BooleanVar()#gradient pcpx
                self.b713=BooleanVar()#gradient pcpf

                self.b8=BooleanVar()#objective pca



                #SAMPLING

                self.l1=Label(self, text="SAMPLING")
                self.l1.grid(row=0,sticky='W')

                self.cb1 = Checkbutton(self, text="Sample",
                    variable=self.b1,command=self.add1)
                self.cb1.grid(row=1,column=0,sticky='W')

                self.l11=Label(self, text="N. points:",state=tk.DISABLED)
                self.l11.grid(row=1,column=0, sticky='E')

                self.e1=Entry(self,textvariable=self.s1,width=5, justify=tk.CENTER,state=tk.DISABLED)
                self.e1.insert(0,'1000')
                self.e1.grid(row=1,column=1,sticky='W')


                self.r11=Radiobutton(self, text='sobol',variable=self.i1, value=0,state=tk.DISABLED)
                self.r11.grid(row=1,column=1,sticky='e')

                self.r12=Radiobutton(self, text='lhs',variable=self.i1, value=1,state=tk.DISABLED)
                self.r12.grid(row=1,column=2,sticky='w')

                #F-DISTRIBUTION

                self.l2=Label(self,text='F-DISTRIBUTION FEATURES')
                self.l2.grid(row=2,sticky='W')

                self.cb2 = Checkbutton(self, text="Plot f-distributions",
                    variable=self.b2)
                self.cb2.grid(row=3,column=0,sticky='W')

                self.l2=Label(self, text="Show percentiles:")
                self.l2.grid(row=3,column=1,sticky='E')

                self.e2=Entry(self,textvariable=self.s2,width=15, justify=tk.CENTER)
                self.e2.insert(0,'0,5,10,25,50,100')
                self.e2.grid(row=3,column=2,sticky='w')

                self.cb20 = Checkbutton(self, text="Print basic info.",
                    variable=self.b20)
                self.cb20.grid(row=3,column=3,sticky='W')

                #DEGREE OF LINEARITY AND CONVEXITY

                self.l3=Label(self,text='LINEARITY AND CONVEXITY')
                self.l3.grid(row=4,sticky='W')

                self.cb3 = Checkbutton(self, text="Perform test",
                    variable=self.b3,command=self.add3)
                self.cb3.grid(row=5,column=0,sticky='W')

                self.l3=Label(self, text="Number of pairs:",state=tk.DISABLED)
                self.l3.grid(row=5,column=1,sticky='E')

                self.e3=Entry(self,textvariable=self.s3,width=5,state=tk.DISABLED, justify=tk.CENTER)
                self.e3.grid(row=5,column=2,sticky='w')

                #META-MODEL FEATURES

                self.l4=Label(self,text='META-MODEL FEATURES')
                self.l4.grid(row=6,sticky='W')

                self.cb41 = Checkbutton(self, text="Linear regression",
                    variable=self.b41)
                self.cb41.grid(row=7,column=0,sticky='W')

                self.cb42 = Checkbutton(self, text="Linear w/ interaction",
                    variable=self.b42,command=self.add42)
                self.cb42.grid(row=8,column=0,sticky='W')

                self.l42=Label(self, text="Order(s) of interaction:",state=tk.DISABLED)
                self.l42.grid(row=8,column=1,sticky='E')

                self.e42=Entry(self,textvariable=self.s42,width=5,state=tk.DISABLED, justify=tk.CENTER)
                self.e42.insert(0,'2')
                self.e42.grid(row=8,column=2,sticky='w')

                self.cb43 = Checkbutton(self, text="Polynomial regression",
                    variable=self.b43,command=self.add43)
                self.cb43.grid(row=9,column=0,sticky='W')

                self.l43=Label(self, text="Degree(s) of regression:",state=tk.DISABLED)
                self.l43.grid(row=9,column=1,sticky='E')

                self.e43=Entry(self,textvariable=self.s43,width=5,state=tk.DISABLED, justify=tk.CENTER)
                self.e43.insert(0,'2')
                self.e43.grid(row=9,column=2,sticky='w')
 

                #MULTI-MODALITY

                self.l5=Label(self, text="LEVELSET FEATURES / MMI")
                self.l5.grid(row=10,sticky='W')

                self.cb51 = Checkbutton(self, text="SVM",
                    variable=self.b51,command=self.add51)
                self.cb51.grid(row=11,column=0,sticky='W')

                self.l51=Label(self, text="Threshold(s):",state=tk.DISABLED)
                self.l51.grid(row=11,column=0,sticky='E')

                self.e51=Entry(self,textvariable=self.s51,state=tk.DISABLED,width=10, justify=tk.CENTER)
                self.e51.grid(row=11,column=1,sticky='w')

                self.cb52 = Checkbutton(self, text="DAC",
                    variable=self.b52,command=self.add52)
                self.cb52.grid(row=12,column=0,sticky='W')

                self.l52=Label(self, text="Threshold(s):",state=tk.DISABLED)
                self.l52.grid(row=12,column=0,sticky='E')

                self.e52=Entry(self,textvariable=self.s52,state=tk.DISABLED,width=10, justify=tk.CENTER)
                self.e52.grid(row=12,column=1,sticky='w')

                self.l53=Label(self, text="K_test:",state=tk.DISABLED)
                self.l53.grid(row=11,column=1,sticky='E')

                self.e53=Entry(self,textvariable=self.s53,state=tk.DISABLED,width=5, justify=tk.CENTER)
                self.e53.grid(row=11,column=2,sticky='w')

                self.l54=Label(self, text="K_tune:",state=tk.DISABLED)
                self.l54.grid(row=11,column=2,sticky='E')

                self.e54=Entry(self,textvariable=self.s54,state=tk.DISABLED,width=5, justify=tk.CENTER)
                self.e54.grid(row=11,column=3,sticky='w')

                self.l55=Label(self, text="K_test:",state=tk.DISABLED)
                self.l55.grid(row=12,column=1,sticky='E')

                self.e55=Entry(self,textvariable=self.s55,state=tk.DISABLED,width=5, justify=tk.CENTER)
                self.e55.grid(row=12,column=2,sticky='w')

                #LOCAL SEARCH
                
                self.l6=Label(self, text="LOCAL SEARCH")
                self.l6.grid(row=13,sticky='W')

                self.cb6 = Checkbutton(self, text="Perform local search",
                    variable=self.b6,command=self.add6)
                self.cb6.grid(row=14,column=0,sticky='W')

                self.l60=Label(self, text="N. initial points:",state=tk.DISABLED)
                self.l60.grid(row=14, column=1,sticky='e')

                self.e6=Entry(self,textvariable=self.s6,state=tk.DISABLED,width=5, justify=tk.CENTER)
                self.e6.grid(row=14,column=2,sticky='w')

                self.cb60 = Checkbutton(self, text="Cluster results",
                    variable=self.b60,command=self.add61,state=tk.DISABLED)
                self.cb60.grid(row=15,column=0,sticky='W')

                self.r61=Radiobutton(self, text="Fix variance ratio:",state=tk.DISABLED,variable=self.i61,value=0,command=self.add62)
                self.r61.grid(row=15,column=1,sticky='w')

                self.e61=Entry(self,textvariable=self.s61,state=tk.DISABLED,width=5, justify=tk.CENTER)
                self.e61.grid(row=15,column=2,sticky='w')

                self.r62=Radiobutton(self, text="Fix number of clusters:",state=tk.DISABLED,variable=self.i61,value=1,command=self.add62)
                self.r62.grid(row=16,column=1,sticky='w')

                self.e62=Entry(self,textvariable=self.s62,state=tk.DISABLED,width=5, justify=tk.CENTER)
                self.e62.grid(row=16,column=2,sticky='w')

                self.cb63 = Checkbutton(self, text="Scatter plot",
                    variable=self.b63,command=self.add63,state=tk.DISABLED)
                self.cb63.grid(row=16,column=3,sticky='W')

                self.l63=Label(self, text="Dim(s):",state=tk.DISABLED)
                self.l63.grid(row=16,column=3,sticky='E')

                self.e63=Entry(self,textvariable=self.s63,state=tk.DISABLED,width=13, justify=tk.CENTER)
                self.e63.grid(row=16,column=4,sticky='w')

                self.cb64 = Checkbutton(self, text="Plot PCP (together)",
                    variable=self.b64,state=tk.DISABLED)
                self.cb64.grid(row=14,column=3,sticky='W')

                self.cb65 = Checkbutton(self, text="Plot PCP (per cluster)",
                    variable=self.b65,state=tk.DISABLED)
                self.cb65.grid(row=15,column=3,sticky='W')

                self.b660 = Button(self, text='Advanced search options',state=tk.DISABLED, command=self.add660)
                self.b660.grid(row=16,column=0,sticky='w')

                self.cb66 = Checkbutton(self, text='Use algorithm ls_algo')

                self.l66=Label(self, text="Decomp.:")

                self.r661=Radiobutton(self, text="Tchebycheff",variable=self.i66,value=0,command=self.add66x)               
                self.r662=Radiobutton(self, text="Bi",variable=self.i66,value=1,command=self.add66x)
                self.r663=Radiobutton(self, text="Weighted",variable=self.i66,value=2,command=self.add66x)

                self.l661=Label(self,text='   weights:')
                self.e661=Entry(self,textvariable=self.s661,width=10,justify=tk.CENTER)
                self.e661.insert(0,'random')
                self.l662=Label(self,text='  Z:')
                self.e662=Entry(self,textvariable=self.s662,width=10,justify=tk.CENTER)
                self.e662.insert(0,'0')


                #CURVATURE

                self.l7=Label(self, text="CURVATURE")
                self.l7.grid(row=18,sticky='W')

                self.l71=Label(self, text="  -Gradient")
                self.l71.grid(row=19, sticky='W')

                self.cb71 = Checkbutton(self, text="Get gradient",
                    variable=self.b71,command=self.add71)
                self.cb71.grid(row=20,column=0,sticky='W')

                self.l711 = Label(self,text='Plots:', state=tk.DISABLED)
                self.l711.grid(row=20,column=0,sticky='e')

                self.cb711 = Checkbutton(self, text="Sparsity",
                    variable=self.b711, state=tk.DISABLED)
                self.cb711.grid(row=20,column=1,sticky='W')

                self.cb712 = Checkbutton(self, text="PCP in X",
                    variable=self.b712, state=tk.DISABLED)
                self.cb712.grid(row=20,column=1,sticky='e')


                self.cb713 = Checkbutton(self, text="PCP in F",
                    variable=self.b713, state=tk.DISABLED)
                self.cb713.grid(row=20,column=2,sticky='W')

                self.l72=Label(self, text="  -Hessian")
                self.l72.grid(row=21, sticky='W')

                self.cb72 = Checkbutton(self, text="Get hessian",
                    variable=self.b72)
                self.cb72.grid(row=22,column=0,sticky='NW')

                #OBJCORR
                self.l8=Label(self, text="OBJECTIVE CORRELATION")
                self.l8.grid(row=23,sticky='W')

                self.cb8 = Checkbutton(self, text="Perform objective \ncorrelation PCA test",
                    variable=self.b8)
                self.cb8.grid(row=24,column=0,sticky='W')

                #GO
                self.go=Button(self,text='< GO >',width=10,height=2,bg='green',activebackground='green',command=self.go)
                self.go.grid(row=24,column=4,sticky='se')

            def add1(self):
                if self.b1.get()==True:
                    self.l11.configure(state=tk.NORMAL)
                    self.e1.configure(state=tk.NORMAL)
                    self.r11.configure(state=tk.NORMAL)
                    self.r12.configure(state=tk.NORMAL)

                else:
                    self.l11.configure(state=tk.DISABLED)
                    self.e1.configure(state=tk.DISABLED)
                    self.r11.configure(state=tk.DISABLED)
                    self.r12.configure(state=tk.DISABLED)

            def add3(self):
                if self.b3.get()==True:
                    self.l3.configure(state=tk.NORMAL)
                    self.e3.configure(state=tk.NORMAL)
                    self.e3.insert(0,'X')

                else:
                    self.l3.configure(state=tk.DISABLED)
                    self.e3.delete(0,5000)
                    self.e3.configure(state=tk.DISABLED)

            def add42(self):
                if self.b42.get()==True:
                    self.l42.configure(state=tk.NORMAL)
                    self.e42.configure(state=tk.NORMAL)
                    self.e42.insert(0,'2')

                else:
                    self.l42.configure(state=tk.DISABLED)
                    self.e42.delete(0,5000)
                    self.e42.configure(state=tk.DISABLED)


            def add43(self):
                if self.b43.get()==True:
                    self.l43.configure(state=tk.NORMAL)
                    self.e43.configure(state=tk.NORMAL)
                    self.e43.insert(0,'2')

                else:
                    self.l43.configure(state=tk.DISABLED)
                    self.e43.delete(0,5000)
                    self.e43.configure(state=tk.DISABLED)

            def add51(self):
                if self.b51.get()==True:
                    self.l51.configure(state=tk.NORMAL)
                    self.e51.configure(state=tk.NORMAL)
                    self.e51.insert(0,'50')
                    self.l53.configure(state=tk.NORMAL)
                    self.e53.configure(state=tk.NORMAL)
                    self.e53.insert(0,'10')
                    self.l54.configure(state=tk.NORMAL)
                    self.e54.configure(state=tk.NORMAL)
                    self.e54.insert(0,'3')
                else:
                    self.l51.configure(state=tk.DISABLED)
                    self.e51.delete(0,5000)
                    self.e51.configure(state=tk.DISABLED)
                    self.l53.configure(state=tk.DISABLED)
                    self.e53.delete(0,5000)
                    self.e53.configure(state=tk.DISABLED)
                    self.l54.configure(state=tk.DISABLED)
                    self.e54.delete(0,5000)                    
                    self.e54.configure(state=tk.DISABLED)


            def add52(self):
                if self.b52.get()==True:
                    self.l52.configure(state=tk.NORMAL)
                    self.e52.configure(state=tk.NORMAL)
                    self.e52.insert(0,'50')
                    self.l55.configure(state=tk.NORMAL)
                    self.e55.configure(state=tk.NORMAL)
                    self.e55.insert(0,'10')
                else:
                    self.l52.configure(state=tk.DISABLED)
                    self.e52.delete(0,5000)
                    self.e52.configure(state=tk.DISABLED)
                    self.l55.configure(state=tk.DISABLED)
                    self.e55.delete(0,5000)
                    self.e55.configure(state=tk.DISABLED)

            def add6(self):
                if self.b6.get()==True:
                    self.r61.configure(state=tk.NORMAL)
                    self.r61.select()
                    self.r62.configure(state=tk.NORMAL)
                    self.e61.configure(state=tk.NORMAL)
                    self.e61.insert(0,'0.95')
                    self.cb60.configure(state=tk.NORMAL)
                    self.cb60.select()
                    self.e62.delete(0,5000)
                    self.e62.configure(state=tk.DISABLED)
                    self.cb63.configure(state=tk.NORMAL)
                    self.cb63.deselect()
                    self.l63.configure(state=tk.DISABLED)
                    self.e63.delete(0,5000)
                    self.e63.configure(state=tk.DISABLED)
                    self.cb64.configure(state=tk.NORMAL)
                    self.cb65.configure(state=tk.NORMAL)
                    self.cb64.deselect()
                    self.cb65.deselect()
                    self.l60.configure(state=tk.NORMAL)
                    self.e6.configure(state=tk.NORMAL)
                    self.e6.insert(0,'X')
                    self.b660.configure(state=tk.NORMAL)

                    self.cb66.pack()
                    self.b660.configure(text='Advanced search options', command=self.add660)
                    self.b660.grid(row=16,column=0,sticky='w')
                    self.l66.pack()
                    self.r661.pack()
                    self.r662.pack()
                    self.r663.pack()
                    self.l661.pack()
                    self.e661.pack()
                    self.l662.pack()
                    self.e662.pack()
                    self.r661.select()
                    self.cb66.deselect()
                    self.e661.delete(0,5000)
                    self.e661.insert(0,'random')
                    self.l662.configure(state=tk.NORMAL)
                    self.e662.configure(state=tk.NORMAL)
                    self.e662.delete(0,5000)
                    self.e662.insert(0,'0')
                else:
                    self.r61.configure(state=tk.DISABLED)
                    self.r62.configure(state=tk.DISABLED)
                    self.e61.delete(0,5000)
                    self.e61.configure(state=tk.DISABLED)
                    self.cb60.deselect()
                    self.cb60.configure(state=tk.DISABLED)
                    self.e62.delete(0,5000)
                    self.e62.configure(state=tk.DISABLED)
                    self.cb63.deselect()
                    self.cb63.configure(state=tk.DISABLED)
                    self.l63.configure(state=tk.DISABLED)
                    self.e63.delete(0,5000)
                    self.e63.configure(state=tk.DISABLED)
                    self.cb64.deselect()
                    self.cb65.deselect()
                    self.cb64.configure(state=tk.DISABLED)
                    self.cb65.configure(state=tk.DISABLED)
                    self.l60.configure(state=tk.DISABLED)
                    self.e6.delete(0,5000)
                    self.e6.configure(state=tk.DISABLED)
                    self.b660.configure(state=tk.DISABLED)

                    self.cb66.pack()
                    self.b660.configure(text='Advanced search options', command=self.add660)
                    self.b660.grid(row=16,column=0,sticky='w')
                    self.l66.pack()
                    self.r661.pack()
                    self.r662.pack()
                    self.r663.pack()
                    self.l661.pack()
                    self.e661.pack()
                    self.l662.pack()
                    self.e662.pack()
                    self.r661.select()
                    self.cb66.deselect()
                    self.e661.delete(0,5000)
                    self.e661.insert(0,'random')
                    self.l662.configure(state=tk.NORMAL)
                    self.e662.configure(state=tk.NORMAL)
                    self.e662.delete(0,5000)
                    self.e662.insert(0,'0')

            def add61(self):
                if self.b60.get()==True:                
                    self.r61.configure(state=tk.NORMAL)
                    self.r61.select()
                    self.r62.configure(state=tk.NORMAL)
                    self.e61.configure(state=tk.NORMAL)
                    self.e61.insert(0,'0.95')
                    self.e62.configure(state=tk.DISABLED)
                    self.cb63.configure(state=tk.NORMAL)
                    self.cb63.deselect()
                    self.l63.configure(state=tk.DISABLED)
                    self.e63.delete(0,5000)
                    self.e63.configure(state=tk.DISABLED)
                    self.cb64.configure(state=tk.NORMAL)
                    self.cb65.configure(state=tk.NORMAL)
                    self.cb64.deselect()
                    self.cb65.deselect()
                else:
                    self.r61.configure(state=tk.DISABLED)
                    self.e61.delete(0,5000)
                    self.e61.configure(state=tk.DISABLED)
                    self.r62.configure(state=tk.DISABLED)
                    self.e62.delete(0,5000)
                    self.e62.configure(state=tk.DISABLED)
                    self.cb63.configure(state=tk.DISABLED)
                    self.cb63.deselect()
                    self.l63.configure(state=tk.DISABLED)
                    self.e63.delete(0,5000)
                    self.e63.configure(state=tk.DISABLED)
                    self.cb64.deselect()
                    self.cb65.deselect()
                    self.cb64.configure(state=tk.DISABLED)
                    self.cb65.configure(state=tk.DISABLED)

            def add62(self):
                if self.i61.get()==0:
                    self.e61.configure(state=tk.NORMAL)
                    if self.e61.get()=='':
                        self.e61.insert(0,'0.95')
                    self.e62.delete(0,500)
                    self.e62.configure(state=tk.DISABLED)
                else:
                    self.e62.configure(state=tk.NORMAL)
                    if self.e62.get()=='':
                        self.e62.insert(0,'10')
                    self.e61.delete(0,500)
                    self.e61.configure(state=tk.DISABLED)

            def add63(self):
                if self.b63.get()==True:
                    self.l63.configure(state=tk.NORMAL)
                    self.e63.delete(0,500)
                    self.e63.configure(state=tk.NORMAL)
                else:
                    self.l63.configure(state=tk.DISABLED)
                    self.e63.delete(0,500)
                    self.e63.configure(state=tk.DISABLED)

            def add660(self):
                self.l66.grid(row=17,column=1,sticky='w')
                self.r661.grid(row=17,column=1,sticky='e')
                self.r662.grid(row=17,column=2,sticky='w')
                self.r663.grid(row=17,column=2,sticky='e')
                self.cb66.grid(row=17,column=0,sticky='w')
                self.b660.configure(text='   Basic search options    ',command=self.add660b)
                self.b660.grid(row=16,column=0,sticky='w')
                self.l661.grid(row=17,column=3,sticky='w')
                self.e661.grid(row=17,column=3,sticky='e')
                self.l662.grid(row=17,column=4,sticky='w')
                self.e662.grid(row=17,column=4,sticky='e')

            def add660b(self):
                self.cb66.pack()
                self.b660.configure(text='Advanced search options', command=self.add660)
                self.b660.grid(row=16,column=0,sticky='w')
                self.l66.pack()
                self.r661.pack()
                self.r662.pack()
                self.r663.pack()
                self.l661.pack()
                self.e661.pack()
                self.l662.pack()
                self.e662.pack()
                self.r661.select()
                self.cb66.deselect()
                self.e661.delete(0,5000)
                self.e661.insert(0,'random')
                self.l662.configure(state=tk.NORMAL)
                self.e662.configure(state=tk.NORMAL)
                self.e662.delete(0,5000)
                self.e662.insert(0,'0')

            def add66x(self):
                if self.i66.get()==2:
                    self.l662.configure(state=tk.DISABLED)
                    self.e662.configure(state=tk.DISABLED)
                else:
                    self.l662.configure(state=tk.NORMAL)
                    self.e662.configure(state=tk.NORMAL)

            def add71(self):
                if self.b71.get()==True:
                    self.l711.configure(state=tk.NORMAL)
                    self.cb711.configure(state=tk.NORMAL)
                    self.cb712.configure(state=tk.NORMAL)
                    self.cb713.configure(state=tk.NORMAL)
                    self.cb711.deselect()
                    self.cb712.deselect()
                    self.cb713.deselect()
                else:
                    self.l711.configure(state=tk.DISABLED)
                    self.cb711.configure(state=tk.DISABLED)
                    self.cb712.configure(state=tk.DISABLED)
                    self.cb713.configure(state=tk.DISABLED)
                    self.cb711.deselect()
                    self.cb712.deselect()
                    self.cb713.deselect()

            def go(self):
                root.destroy()

        root = Tk()
        root.geometry("750x550")
        app = parameters(root)
        root.mainloop()

        b1=app.b1.get()

        if b1:
            s1=int(app.s1.get())
            i1=app.i1.get()
        else:
            s1=0
            i1=0

        b2=app.b2.get()
        b20=app.b20.get()
        s2=app.s2.get()
        if len(s2)>0:
            s2=[float(i) for i in s2[:].split(',')]
        else:
            s2=[]

        b3=app.b3.get()
        if b3:
            s3=app.s3.get()
            if s3=='X':
                s3=self.npoints
            else:
                s3=int(s3)
        else:
            s3=0

        b41=app.b41.get()
        b42=app.b42.get()
        s42=app.s42.get()
        if b42 and len(s42)>0:
            s42=[int(i) for i in s42[:].split(',')]
        b43=app.b43.get()
        s43=app.s43.get()
        if b43 and len(s43)>0:
            s43=[int(i) for i in s43[:].split(',')]

        b51=app.b51.get()
        s51=app.s51.get()
        if b51 and len(s51)>0:
            s51=[float(i) for i in s51[:].split(',')]
            s53=int(app.s53.get())
            s54=int(app.s54.get())
        else:
            s51=[]
            s53=app.s53.get()
            s54=app.s54.get()
        b52=app.b52.get()
        s52=app.s52.get()
        if b52 and len(s52)>0:
            s52=[float(i) for i in s52[:].split(',')]
            s55=int(app.s55.get())
        else:
            s52=[]
            s55=app.s55.get()
        b6=app.b6.get()
        s6=app.s6.get()
        i66=app.i66.get()
        if i66==0:
            i66='tchebycheff'
        elif i66==1:
            i66=='bi'
        else:
            i66=='weighted'
        s661=app.s661.get()
        s662=app.s662.get()
        if b6:
            if s661!='random' and s661!='uniform' and len(s661)>0:
                s661=[float(i) for i in s661[:].split(',')]
            if s662=='0':
                s662=[]
            elif len(s662)>0:
                s662=[float(i) for i in s662[:].split(',')]
            if s6=='X':
                s6=self.npoints
            else:
                s6=int(s6)
        b60=app.b60.get()
        i61=app.i61.get()
        s61=app.s61.get()
        s62=app.s62.get()
        b63=app.b63.get()
        s63=app.s63.get()
        b64=app.b64.get()
        b65=app.b65.get()
        b66=app.b66.get()
        if b60:
            if i61==0:
                s61=float(s61)
            else:
                s62=int(s62)
            if b63 and len(s63)>0:
                s63=[int(i) for i in s63[:].split(',')]
        b71=app.b71.get()
        b72=app.b72.get()
        b711=app.b711.get()
        b712=app.b712.get()
        b713=app.b713.get()
        b8=app.b8.get()

        self._print_report(b1=b1,sample=s1,p_f=s2,b2=b2,b20=b20,p_svm=s51,p_dac=s52,local_search=b6,\
        gradient=b71,hessian=b72,b3=b3,b41=b41,b42=b42,b43=b43,b51=b51,b52=b52,b60=b60,b63=b63,b64=b64,b65=b65,b66=b66,\
        b711=b711,b712=b712,b713=b713,i1=i1,s3=s3,s42=s42,s43=s43,s51=s51,s52=s52,s53=s53,s54=s54,s55=s55,s6=s6,\
        i61=i61,s61=s61,s62=s62,s63=s63,i66=i66,s661=s661,s662=s662,save=False,pca=b8)