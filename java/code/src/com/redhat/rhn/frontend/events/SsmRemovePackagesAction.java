/**
 * Copyright (c) 2009 Red Hat, Inc.
 *
 * This software is licensed to you under the GNU General Public License,
 * version 2 (GPLv2). There is NO WARRANTY for this software, express or
 * implied, including the implied warranties of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
 * along with this software; if not, see
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
 *
 * Red Hat trademarks are not licensed under GPLv2. No permission is
 * granted to use or replicate Red Hat trademarks that are incorporated
 * in this software or its documentation.
 */
package com.redhat.rhn.frontend.events;

import com.redhat.rhn.common.db.datasource.DataResult;

import com.redhat.rhn.common.localization.LocalizationService;

import com.redhat.rhn.common.messaging.EventMessage;

import com.redhat.rhn.domain.server.Server;
import com.redhat.rhn.domain.server.ServerFactory;

import com.redhat.rhn.domain.user.User;
import com.redhat.rhn.domain.user.UserFactory;

import com.redhat.rhn.frontend.dto.PackageListItem;

import com.redhat.rhn.manager.action.ActionManager;

import com.redhat.rhn.manager.ssm.SsmOperationManager;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.apache.log4j.Logger;

/**
 * Handles removing packages from servers in the SSM.
 *
 * @see com.redhat.rhn.frontend.events.SsmRemovePackagesEvent
 * @version $Revision$
 */
public class SsmRemovePackagesAction extends AbstractDatabaseAction {
    private static Logger log = Logger.getLogger(SsmRemovePackagesAction.class);

    /** {@inheritDoc} */
    protected void doExecute(EventMessage msg) {
        log.debug("Executing package removals.");
        SsmRemovePackagesEvent event = (SsmRemovePackagesEvent) msg;

        DataResult result = event.getResult();
        User user = UserFactory.lookupById(event.getUserId());
        Date earliest = event.getEarliest();

        LocalizationService ls = LocalizationService.getInstance();
        long operationId = SsmOperationManager.createOperation(user,
            ls.getMessage("ssm.package.remove.operationname"), null);
        int numPackages = 0;

        /* 443500 - The following was changed to be able to stuff all of the package
           removals into a single action. The schedule package removal page will display
           a fine grained mapping of server to package removed (taking into account to
           only show packages that exist on the server).

           However, there is no issue in requesting a client delete a package it doesn't
           have. So when we create the action, populate it with all packages and for
           every server to which any package removal applies. This will let us keep all
           of the removals coupled under a single scheduled action and won't cause an
           issue on the client when the scheduled removals are picked up.

           jdobies, Apr 8, 2009
         */

        // The package collection is a set to prevent duplciates when keeping a running
        // total of all packages selected
        Set<PackageListItem> allPackages = new HashSet<PackageListItem>();

        // Looking up all the server objects in Hibernate was *brutally* slow here:
        List<Long> allServerIds = new LinkedList<Long>();

        // Iterate the data, which is essentially each unique package/server combination
        // to remove. Note that this is only for servers that we have marked as having the
        // package installed.
        log.debug("Iterating data.");
        for (Iterator it = result.iterator(); it.hasNext();) {

            // Add action for each package found in the elaborator
            Map data = (Map) it.next();

            // Load the server
            Long sid = (Long)data.get("id");
            allServerIds.add(sid);

            // Get the packages out of the elaborator
            List elabList = (List) data.get("elaborator0");
            numPackages += elabList.size();

            for (Iterator elabIt = elabList.iterator(); elabIt.hasNext();) {
                Map elabData = (Map) elabIt.next();
                String idCombo = (String) elabData.get("id_combo");
                PackageListItem item = PackageListItem.parse(idCombo);
                allPackages.add(item);
            }
        }

        List<Server> allServers = new ArrayList<Server>(result.size());
        allServers.addAll(ServerFactory.lookupByIdsAndUser(allServerIds, user));

        log.debug("Converting data to maps.");
        List<PackageListItem> allPackagesList = new ArrayList<PackageListItem>(allPackages);
        List<Map<String, Long>> packageListData =
            PackageListItem.toKeyMaps(allPackagesList);

        log.debug("Scheduling package removals.");
        ActionManager.schedulePackageRemoval(user, allServers, packageListData, earliest);
        log.debug("Done.");
    }

}

