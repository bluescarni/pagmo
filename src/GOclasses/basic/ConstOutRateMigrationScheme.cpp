/*****************************************************************************
 *   Copyright (C) 2008, 2009 Advanced Concepts Team (European Space Agency) *
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

#include "ConstOutRateMigrationScheme.h"
#include <iostream>

// 09/03/2009: Initial version by Marek Rucinski.

void ConstOutRateMigrationScheme::preEvolutionCallback(island& _island)
{
	// Update _island's population with individuals from it's inbox.
	
	lock_type lock(topology_mutex);
	
	//std::cout << "preEvolutionCallback( " << _island.id() << " )" << std::endl;

	// Get individuals from the island's inbox
	std::vector<Individual> immigrants = inbox[_island.id()];
	
	//std::cout << immigrants.size() << " individuals available in the inbox!" << std::endl;
	
	if(immigrants.size() > 0) {
		_island.acceptMigratingIndividuals(immigrants); // Accept new individuals
		
		inbox[_island.id()].clear(); // Empty the inbox
	}
}

void ConstOutRateMigrationScheme::postEvolutionCallback(island& _island)
{
	// Choose a random destination neighbour and perform the migration.
	
	lock_type lock(topology_mutex);
	
	//std::cout << "postEvolutionCallback( " << _island.id() << " )" << std::endl;
	
	const std::vector<size_t>& neighbours = topology->get_neighbours_out(_island.id());
	
	//std::cout << "The island has " << neighbours.size() << " neigbours." << std::endl;
	
	if(neighbours.size() > 0) { //the island must have neighbours
		//Draw a neighbour
		size_t chosenNeighbourIndex = rng() % neighbours.size();
		size_t chosenNeighbour = neighbours[chosenNeighbourIndex];
		
		//std::cout << "Randomly chosen neighbour id: " << chosenNeighbour << std::endl;
		
		//Add migrating individuals to neighbour's inbox
		
		std::vector<Individual> immigrants = _island.getMigratingIndividuals();
		
		//std::cout << "The neighbour receives " << immigrants.size() << " individuals" << std::endl;
		
		if(immigrants.size() > 0) { //if there's anything to migrate, do it
			inbox[chosenNeighbour].insert(inbox[chosenNeighbour].end(), immigrants.begin(), immigrants.end());			
		}
		
		//std::cout << "The size of the neighbour's inbox is now "  << inbox[chosenNeighbour].size() << std::endl;
	}
}

void ConstOutRateMigrationScheme::reset()
{
	inbox.clear();	
	MigrationScheme::reset();	
}
