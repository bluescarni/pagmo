/*****************************************************************************
 *   Copyright (C) 2004-2013 The PaGMO development team,                     *
 *   Advanced Concepts Team (ACT), European Space Agency (ESA)               *
 *   http://apps.sourceforge.net/mediawiki/pagmo                             *
 *   http://apps.sourceforge.net/mediawiki/pagmo/index.php?title=Developers  *
 *   http://apps.sourceforge.net/mediawiki/pagmo/index.php?title=Credits     *
 *   act@esa.int                                                             *
 *                                                                           *
 *   This program is free software; you can redistribute it and/or modify    *
 *   it under the terms of the GNU General Public License as published by    *
 *   the Free Software Foundation; either version 2 of the License, or       *
 *   (at your option) any later version.                                     *
 *                                                                           *
 *   This program is distributed in the hope that it will be useful,         *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of          *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           *
 *   GNU General Public License for more details.                            *
 *                                                                           *
 *   You should have received a copy of the GNU General Public License       *
 *   along with this program; if not, write to the                           *
 *   Free Software Foundation, Inc.,                                         *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.               *
 *****************************************************************************/

#ifndef PAGMO_MPI_ISLAND_H
#define PAGMO_MPI_ISLAND_H

#include <boost/scoped_ptr.hpp>
#include <boost/thread/condition_variable.hpp>
#include <boost/thread/mutex.hpp>
#include <list>
#include <set>
#include <string>

#include "base_island.h"
#include "config.h"
#include "algorithm/base.h"
#include "migration/base_r_policy.h"
#include "migration/base_s_policy.h"
#include "migration/best_s_policy.h"
#include "migration/fair_r_policy.h"
#include "population.h"
#include "problem/base.h"
#include "serialization.h"

// Forward declarations.
namespace pagmo {

class mpi_island;

}

namespace boost { namespace serialization {

template <class Archive>
void save_construct_data(Archive &, const pagmo::mpi_island *, const unsigned int);

template <class Archive>
inline void load_construct_data(Archive &, pagmo::mpi_island *, const unsigned int);

}}

namespace pagmo
{

/// MPI island class.
/**
 * This island class will dispatch evolutions to participants to an MPI cluster. This class can be used like any other island class,
 * the only difference being that before calling any evolution a pagmo::mpi_environment instance must have been created.
 * More information about the MPI support in PaGMO is available in \ref mpi_support "this page".
 * 
 * <b>NOTE</b>: this class is available only if PaGMO was compiled with MPI support.
 *
 * @author Francesco Biscani (bluescarni@gmail.com)
 * @author Dante Stroe (dante.stroe@gmail.com)
 */
class __PAGMO_VISIBLE mpi_island: public base_island
{
		template <class Archive>
		friend void boost::serialization::save_construct_data(Archive &, const pagmo::mpi_island *, const unsigned int);
		template <class Archive>
		friend void boost::serialization::load_construct_data(Archive &, pagmo::mpi_island *, const unsigned int);
	public:
		mpi_island(const mpi_island &);
		explicit mpi_island(const algorithm::base &, const problem::base &, int = 0,
			const double & = 1,
			const migration::base_s_policy & = migration::best_s_policy(),
			const migration::base_r_policy & = migration::fair_r_policy());
		explicit mpi_island(const algorithm::base &, const population &,
			const double & = 1,
			const migration::base_s_policy & = migration::best_s_policy(),
			const migration::base_r_policy & = migration::fair_r_policy());
		mpi_island &operator=(const mpi_island &);
		base_island_ptr clone() const;
	protected:
		void perform_evolution(const algorithm::base &, population &) const;
	public:
		std::string get_name() const;
	private:
		friend class boost::serialization::access;
		template <class Archive>
		void serialize(Archive &ar, const unsigned int)
		{
			// Join is already done in base_island.
			ar & boost::serialization::base_object<base_island>(*this);
		}
		static void init_processors();
		int acquire_processor() const;
		void release_processor(int) const;
	private:
		static boost::mutex				m_proc_mutex;
		static boost::condition_variable		m_proc_cond;
		static boost::mutex				m_mpi_mutex;
		static boost::scoped_ptr<std::set<int> >	m_available_processors;
		static std::list<mpi_island const *>		m_queue;
};

}

namespace boost { namespace serialization {

template <class Archive>
inline void save_construct_data(Archive &ar, const pagmo::mpi_island *isl, const unsigned int)
{
	// Save data required to construct instance.
	pagmo::algorithm::base_ptr algo = isl->m_algo->clone();
	pagmo::problem::base_ptr prob = isl->m_pop.problem().clone();
	ar << algo;
	ar << prob;
}

template <class Archive>
inline void load_construct_data(Archive &ar, pagmo::mpi_island *isl, const unsigned int)
{
	// Retrieve data from archive required to construct new instance.
	pagmo::algorithm::base_ptr algo;
	pagmo::problem::base_ptr prob;
	ar >> algo;
	ar >> prob;
	// Invoke inplace constructor to initialize instance of the algorithm.
	::new(isl)pagmo::mpi_island(*algo,*prob);
}

}} //namespaces

BOOST_CLASS_EXPORT_KEY(pagmo::mpi_island)

#endif
