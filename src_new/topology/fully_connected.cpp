/*****************************************************************************
 *   Copyright (C) 2004-2009 The PaGMO development team,                     *
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

#include <utility>

#include "fully_connected.h"

namespace pagmo { namespace topology {

/// Default constructor.
fully_connected::fully_connected():base() {}

/// Clone method.
base_ptr fully_connected::clone() const
{
	return base_ptr(new fully_connected(*this));
}

/// Connect method.
/**
 * After each push_back(), the new island will be connected to each other island and vice-versa.
 */
void fully_connected::connect(int n)
{
	const v_iterator it_n = get_it(n);
	for (std::pair<v_iterator,v_iterator> vertices = get_vertices_it(); vertices.first != vertices.second; ++vertices.first) {
		// Do not connect with self.
		if (it_n != vertices.first) {
			add_edge(it_n,vertices.first);
			add_edge(vertices.first,it_n);
		}
	}
}

}}