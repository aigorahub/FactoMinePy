dimdesc <- function (res, axes = 1:3, proba = 0.05) 
{
    if (!inherits(res, "PCA") & !inherits(res, "CA") & !inherits(res, "MCA") & !inherits(res, 
        "MFA") & !inherits(res, "HMFA") & !inherits(res, "DMFA") &  !inherits(res, "FAMD")) 
        stop("non convenient data")
      if (inherits(res, "CA")) {
          result <- structure(vector(mode = "list", length = length(axes)), names = colnames(res$row$coord)[axes])
		  tableau <- res$row$coord[,axes,drop=FALSE]
          if (!is.null(res$call$row.sup))  tableau <- rbind.data.frame(tableau,res$row.sup$coord[,axes,drop=FALSE])	
		  tableaucol <- res$col$coord[, axes,drop=FALSE]
          if (!is.null(res$call$col.sup))  tableaucol <- rbind.data.frame(tableaucol,res$col.sup$coord[,axes,drop=FALSE])	
          for (k in 1:length(axes)) {
		    tab <- tableau[order(tableau[,k,drop=FALSE]),k,drop=FALSE]
		    colnames(tab) <- "coord"
            sup <- NULL
		    if (!is.null(c(res$call$quanti.sup,res$call$quali.sup))) {
			  w <- res$call$marge.row*length(res$call$marge.row)
			  if (is.null(res$call$row.sup)) sup <- condes(cbind.data.frame(res$row$coord[,axes[k],drop=FALSE],res$call$Xtot[,c(res$call$quali.sup,res$call$quanti.sup),drop=FALSE]),1,weights=w,proba=proba)
			  else sup <- condes(cbind.data.frame(res$row$coord[,drop=FALSE],res$call$Xtot[-res$call$row.sup,c(res$call$quali.sup,res$call$quanti.sup),drop=FALSE]),1,weights=w,proba=proba)
			}
		    tabcol <- tableaucol[order(tableaucol[,k,drop=FALSE]),k,drop=FALSE]
		    colnames(tabcol) <- "coord"
			result[[k]] <- list(row=tab,col=tabcol)
		    if (!is.null(sup$quanti)) {
			  result[[k]][[length(result[[k]])+1]] <- sup$quanti
			  names(result[[k]])[length(result[[k]])] <- "quanti"   ## attention, c'est bien k ici car la list s'est allongee avant
			}
		    if (!is.null(sup$quali)) {
			  result[[k]][[length(result[[k]])+1]] <- sup$quali
			  names(result[[k]])[length(result[[k]])] <- "quali"   ## attention, c'est bien k ici car la list s'est allongee avant
			}
		    if (!is.null(sup$category)) {
			  result[[k]][[length(result[[k]])+1]] <- sup$category
			  names(result[[k]])[length(result[[k]])] <- "category"   ## attention, c'est bien k ici car la list s'est allongee avant
			}
		  }
      } else {
        ind.supp <- res$call$ind.sup
        result <- structure(vector(mode = "list", length = length(axes)), names = colnames(res$ind$coord)[axes])
        for (k in 1:length(axes)) {
            if (!is.null(ind.supp)) tableau <- cbind.data.frame(res$ind$coord[, axes[k],drop=FALSE], res$call$X[-ind.supp, ])
            else tableau <- cbind.data.frame(res$ind$coord[, axes[k],drop=FALSE], res$call$X)
            result[[k]] <- condes(tableau, 1, proba = proba, weights=res$call$row.w.init)
			if (k==1) result$call <- result[[1]]$call
			result[[k]]$call <- NULL
        }
    }
    class(result) <- c("dimdesc", "list")
    return(result)
}